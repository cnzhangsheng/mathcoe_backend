"""
PDF generation utilities for exam paper export
"""
import base64
import io
import json
import logging
import os
import re
import struct
from pathlib import Path
from urllib.parse import urlparse
import urllib.request

logger = logging.getLogger(__name__)

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
                data = f.read()
            logger.debug(f"PDF图片: 本地读取成功 filename={filename}, size={len(data)}")
            return data
        logger.debug(f"PDF图片: 本地文件不存在 path={local_path}, 尝试HTTP")
    try:
        req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            logger.debug(f"PDF图片: HTTP读取成功 url={img_url[:60]}, size={len(data)}")
            return data
    except Exception as e:
        logger.warning(f"PDF图片: HTTP读取失败 url={img_url[:60]}, error={e}")
        return None


def _img_bytes_to_data_uri(img_data: bytes, img_url: str) -> str:
    """Convert image bytes to a base64 data URI, inferring MIME from URL."""
    ext = img_url.rsplit(".", 1)[-1].lower() if "." in img_url else "png"
    mime = _MIME_TYPES.get(ext, "image/png")
    return f"data:{mime};base64,{base64.b64encode(img_data).decode()}"


def _load_image(img_url: str) -> tuple[str, int | None, int | None]:
    """Return (data_uri, width, height) for an image URL."""
    data = _read_image_bytes(img_url)
    if data is None:
        logger.warning(f"PDF图片: 读取失败，使用原始URL url={img_url[:60]}")
        return (img_url, None, None)
    data_uri = _img_bytes_to_data_uri(data, img_url)
    w, h = _get_image_dimensions(data)
    if w and h:
        logger.debug(f"PDF图片: 尺寸解析成功 url={img_url[:60]}, w={w}, h={h}")
    else:
        logger.warning(f"PDF图片: 尺寸解析失败 url={img_url[:60]}")
    return (data_uri, w, h)


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


# 只匹配百分比值（如 50%、100%）的 width/height，保留 px 像素值
_IMG_STYLE_STRIP_RE = re.compile(r'\b(width|height)\s*:\s*[^;]*%[^;]*;?\s*', re.IGNORECASE)

def _strip_img_style_width(html_text: str) -> str:
    """Remove percentage-based width & height from inline style on <img> tags.

    Percentage values (e.g. width: 50%) are stripped because they depend on
    container layout and produce wrong sizes in PDF. Pixel values (e.g.
    width: 200px) are preserved so user-specified image dimensions take effect.
    """
    _tag_re = re.compile(r'(<img\s[^>]*?style\s*=\s*")([^"]*)("[^>]*?>)', re.IGNORECASE)
    def _clean(m):
        return f'{m.group(1)}{_IMG_STYLE_STRIP_RE.sub("", m.group(2)).strip()}{m.group(3)}'
    return _tag_re.sub(_clean, html_text)


def _inline_images_in_html(html_text: str) -> str:
    """Replace all <img src=\"...\"> with base64 data URIs in HTML content."""
    pattern = re.compile(r'(<img\s[^>]*?src\s*=\s*")([^"]+)("[^>]*?>)', re.IGNORECASE)

    def _replace(match):
        prefix = match.group(1)
        src = match.group(2)
        suffix = match.group(3)
        data_uri = _img_url_to_data_uri(src)
        return f"{prefix}{data_uri}{suffix}"

    html_text = pattern.sub(_replace, html_text)
    html_text = _strip_img_style_width(html_text)
    return html_text


def _inline_content_images(html_text: str) -> str:
    """Replace content <img> with data URIs + aspect-ratio-based max-width.

    If an img tag has explicit pixel dimensions (style="width: Xpx..." or width/height
    attributes), those dimensions are preserved and only the src is replaced.
    Otherwise, applies max-width based on aspect ratio:
      - width > height × 3  → 95% (ultra-wide)
      - width > height × 1.5 → 70% (wide)
      - else → 50% (square/portrait)
    """
    pattern = re.compile(r'(<img\s)([^>]*?)(>)', re.IGNORECASE)
    _src_re = re.compile(r'src\s*=\s*"([^"]+)"', re.IGNORECASE)
    _style_re = re.compile(r'style\s*=\s*"[^"]*"', re.IGNORECASE)
    _width_re = re.compile(r'\bwidth\s*=\s*"[^"]*"', re.IGNORECASE)
    _height_re = re.compile(r'\bheight\s*=\s*"[^"]*"', re.IGNORECASE)
    _px_style_re = re.compile(r'width\s*:\s*[\d.]+px', re.IGNORECASE)

    def _replace(match):
        attrs = match.group(2)
        src_m = _src_re.search(attrs)
        if not src_m:
            return match.group(0)  # no src, leave as-is

        src = src_m.group(1)
        data_uri, w, h = _load_image(src)

        # Check for explicit pixel dimensions (preserve them if found)
        style_m = _style_re.search(attrs)
        has_px_style = style_m and _px_style_re.search(style_m.group(0))
        has_num_w_attr = _width_re.search(attrs) is not None

        if has_px_style or has_num_w_attr:
            # Preserve explicit dimensions, only update src to data URI
            new_src = f'src="{data_uri}"'
            rest = _src_re.sub(new_src, attrs)
            return f'{match.group(1)}{rest}{match.group(3)}'

        # No explicit dimensions — strip existing style/width/height attributes
        clean = _style_re.sub('', attrs)
        clean = _width_re.sub('', clean)
        clean = _height_re.sub('', clean)

        # Determine max-width based on aspect ratio
        if w and h:
            if w > h * 3:
                max_w = "95%"
            elif w > h * 1.5:
                max_w = "70%"
            else:
                max_w = "50%"
        else:
            max_w = "50%"

        new_src = f'src="{data_uri}"'
        new_style = f'style="max-width: {max_w}; height: auto;"'
        return f'{match.group(1)}{new_src} {clean.strip()} {new_style}{match.group(3)}'

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
    logger.info(f"PDF生成: 开始处理 title={title}, questions={len(questions)}")
    for i, q in enumerate(questions):
        content = _parse_json_field(q.get("content"))
        options_raw = _parse_json_list(q.get("options"))
        explanation = _parse_json_field(q.get("explanation"))

        q_id = q.get("id", q.get("_id", i))
        logger.debug(f"PDF题目[{i}]: id={q_id}, options_count={len(options_raw)}")

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

        # Determine grid columns for options layout
        if max_img_w == 0:
            # 纯文字选项：按总字数分档
            total_chars = sum(
                len(opt.get("label", opt.get("key", ""))) +
                len(re.sub(r'<[^>]+>', '', str(opt.get("text", opt.get("value", "")) or "")))
                for opt in options_raw
            )
            if total_chars > 60:
                grid_cols = 1
            elif total_chars > 30:
                grid_cols = 3
            else:
                grid_cols = 0
        else:
            # 含图片选项：固定 3 列
            grid_cols = 3

        logger.debug(f"PDF题目[{i}]: grid_cols={grid_cols}, max_img_w={max_img_w}")

        processed.append({
            "content_text": _inline_content_images((content or {}).get("text", "")),
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

    logger.info(f"PDF生成: HTML渲染完成 title={title}, html_size={len(html)}")

    pdf_bytes = HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf()
    logger.info(f"PDF生成: 完成 title={title}, pdf_size={len(pdf_bytes)}字节")
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
