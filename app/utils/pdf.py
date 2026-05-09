"""
PDF generation utilities for exam paper export
"""
import base64
import io
import json
import os
import re
import struct
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


def _get_image_dimensions(data: bytes) -> tuple[int, int] | None:
    """Parse image dimensions from PNG or JPEG binary data (stdlib only)."""
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        # PNG: IHDR chunk at bytes 16-23 (width, height as big-endian uint32)
        w, h = struct.unpack('>II', data[16:24])
        return w, h
    if data[:2] == b'\xff\xd8':
        # JPEG: scan for SOF0/SOF1/SOF2 marker
        i = 2
        while i < len(data) - 1:
            if data[i] == 0xFF and data[i + 1] in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack('>HH', data[i + 5:i + 9])
                return w, h
            i += 1
    return None


def _read_image_bytes(img_url: str) -> bytes | None:
    """Read image bytes from local filesystem or HTTP URL."""
    parsed = urlparse(img_url)
    path = parsed.path
    if "/static/uploads/" in path:
        filename = path.rsplit("/static/uploads/", 1)[-1]
        local_path = os.path.join(_STATIC_UPLOAD_DIR, filename)
        if os.path.exists(local_path):
            with open(local_path, "rb") as f:
                return f.read()
    try:
        req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read()
    except Exception:
        return None


def _img_bytes_to_data_uri(img_data: bytes, img_url: str) -> str:
    """Convert image bytes to a base64 data URI, inferring MIME from URL."""
    ext = img_url.rsplit(".", 1)[-1].lower() if "." in img_url else "png"
    mime = _MIME_TYPES.get(ext, "image/png")
    return f"data:{mime};base64,{base64.b64encode(img_data).decode()}"


_IMG_CACHE: dict[str, tuple[str, int | None, int | None]] = {}


def _load_image(img_url: str) -> tuple[str, int | None, int | None]:
    """Return (data_uri, width, height) for an image URL.

    Results are cached to avoid re-downloading the same URL.
    """
    if img_url in _IMG_CACHE:
        return _IMG_CACHE[img_url]
    data = _read_image_bytes(img_url)
    if data is None:
        result = (img_url, None, None)
    else:
        data_uri = _img_bytes_to_data_uri(data, img_url)
        w, h = _get_image_dimensions(data)
        result = (data_uri, w, h)
    _IMG_CACHE[img_url] = result
    return result


def _make_absolute_url(img_url: str) -> str:
    """Convert relative image URL to absolute"""
    if img_url.startswith(("http://", "https://")):
        return img_url
    base = settings.server_host.rstrip("/")
    if img_url.startswith("/"):
        return f"{base}{img_url}"
    return f"{base}/{img_url}"


def _img_url_to_data_uri(img_url: str) -> str:
    """Convert an image URL to a base64 data URI (uses cached loader)."""
    data_uri, _, _ = _load_image(img_url)
    return data_uri


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
                content_images = [_img_url_to_data_uri(_make_absolute_url(img)) for img in raw_images]

        # Process options and determine layout
        processed_options = []
        max_img_w = 0

        # Regex to extract <img src="..."> from option text
        _img_src_re = re.compile(r'<img[^>]+src="([^"]+)"', re.IGNORECASE)

        for opt in options_raw:
            key = opt.get("label", opt.get("key", ""))
            raw_text = opt.get("text", opt.get("value", "")) or ""

            # Strip <p> tags from rich text — they cause unwanted line breaks in PDF
            raw_text = re.sub(r'</?p[^>]*>', '', raw_text, flags=re.IGNORECASE)

            # Check for images embedded in option text
            text_img_urls = _img_src_re.findall(str(raw_text))
            # Check for separate image field (old data format)
            separate_img_url = opt.get("image")

            # Get dimensions from text images (for grid_cols decision)
            for img_url in text_img_urls:
                abs_url = _make_absolute_url(img_url)
                _, w, h = _load_image(abs_url)
                if w and w > max_img_w:
                    max_img_w = w

            # Get dimensions from separate image field
            img_data = None
            if separate_img_url:
                abs_url = _make_absolute_url(separate_img_url)
                data_uri, w, h = _load_image(abs_url)
                img_data = {"src": data_uri, "width": w, "height": h}
                if w and w > max_img_w:
                    max_img_w = w

            value = _inline_images_in_html(raw_text)

            processed_options.append({
                "key": key,
                "value": value,
                "image_data": img_data,  # only set for separate image field
            })

        # Determine grid columns based on max image width.
        # 3 columns preferred; fall back to 2 for wide images.
        # A4 content ~539pt; 3-col cell ~174pt, 2-col cell ~265pt.
        if max_img_w == 0:
            grid_cols = 0  # text-only → inline layout
        elif max_img_w > 350:
            grid_cols = 2
        else:
            grid_cols = 3

        processed.append({
            "content_text": _inline_images_in_html((content or {}).get("text", "")),
            "content_images": content_images,
            "options": processed_options,
            "grid_cols": grid_cols,
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
