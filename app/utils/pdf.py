"""
PDF generation utilities for exam paper export
"""
import base64
import io
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse
import urllib.request

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.core.config import settings

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

# Supported image MIME types
_MIME_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
    "svg": "image/svg+xml",
}

# Base path for static uploads (app/static/uploads)
_STATIC_UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),  # app/
    "static",
    "uploads",
)


def _img_url_to_data_uri(img_url: str) -> str:
    """Convert an image URL to a base64 data URI.
    Tries local filesystem first, then falls back to HTTP download.
    """
    # --- Try local filesystem ---
    parsed = urlparse(img_url)
    # Match URLs pointing to our own static uploads
    path = parsed.path
    if "/static/uploads/" in path:
        filename = path.rsplit("/static/uploads/", 1)[-1]
        local_path = os.path.join(_STATIC_UPLOAD_DIR, filename)
        if os.path.exists(local_path):
            with open(local_path, "rb") as f:
                img_data = f.read()
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"
            mime = _MIME_TYPES.get(ext, "image/png")
            return f"data:{mime};base64,{base64.b64encode(img_data).decode()}"

    # --- Fallback: HTTP download ---
    try:
        req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            img_data = resp.read()
        content_type = resp.headers.get("Content-Type", "image/png")
        return f"data:{content_type};base64,{base64.b64encode(img_data).decode()}"
    except Exception:
        return img_url  # fallback: keep original URL


def _inline_images_in_html(html_text: str) -> str:
    """Replace all <img src=\"...\"> with base64 data URIs in HTML content."""
    pattern = re.compile(r'(<img\s[^>]*?src\s*=\s*")([^"]+)("[^>]*?>)', re.IGNORECASE)

    def _replace(match):
        prefix = match.group(1)
        src = match.group(2)
        suffix = match.group(3)
        data_uri = _img_url_to_data_uri(src)
        return f"{prefix}{data_uri}{suffix}"

    return pattern.sub(_replace, html_text)


def _parse_json_field(value: str | dict | None) -> dict | None:
    """Parse a JSON field that might be a string or dict"""
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def _parse_json_list(value: str | list | None) -> list:
    """Parse a JSON list field that might be a string or list"""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _make_absolute_url(img_url: str) -> str:
    """Convert relative image URL to absolute"""
    if img_url.startswith(("http://", "https://")):
        return img_url
    base = settings.server_host.rstrip("/")
    if img_url.startswith("/"):
        return f"{base}{img_url}"
    return f"{base}/{img_url}"


def render_exam_paper_pdf(
    title: str,
    difficulty_level: int,
    description: str | None,
    questions: list[dict],
) -> bytes:
    """Render an exam paper as PDF bytes.

    Each question dict should contain:
        - content (str | dict | None): question content JSON (text + optional images)
        - options (str | list | None): options JSON list
        - explanation (str | dict | None): explanation JSON (text + optional format)
        - answer (str): correct answer key
    """
    processed = []
    for q in questions:
        content = _parse_json_field(q.get("content"))
        options_raw = _parse_json_list(q.get("options"))
        explanation = _parse_json_field(q.get("explanation"))

        # Process images in content
        content_images = []
        if content and "images" in content:
            raw_images = content["images"]
            if isinstance(raw_images, list):
                content_images = [_make_absolute_url(img) for img in raw_images]

        processed.append({
            "content_text": _inline_images_in_html((content or {}).get("text", "")),
            "content_images": [_img_url_to_data_uri(_make_absolute_url(img)) for img in content_images],
            "options": [
                {
                    "key": opt.get("label", opt.get("key", "")),
                    "value": _inline_images_in_html(opt.get("text", opt.get("value", ""))),
                    "image": _img_url_to_data_uri(_make_absolute_url(opt["image"])) if opt.get("image") else None,
                }
                for opt in options_raw
            ],
            "explanation_text": (explanation or {}).get("text", ""),
            "correct_answer": q.get("answer", ""),
        })

    template = _env.get_template("exam_paper_pdf.html")
    html = template.render(
        paper={
            "title": title,
            "difficulty_level": difficulty_level,
            "description": description or "",
        },
        questions=processed,
    )

    pdf_bytes = HTML(string=html).write_pdf()
    return pdf_bytes


def render_exam_paper_pdf_stream(
    title: str,
    difficulty_level: int,
    description: str | None,
    questions: list[dict],
) -> io.BytesIO:
    """Render exam paper as PDF and return a BytesIO stream."""
    pdf_bytes = render_exam_paper_pdf(title, difficulty_level, description, questions)
    return io.BytesIO(pdf_bytes)
