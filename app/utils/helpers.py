"""
Helper utilities
"""
import re
import uuid

from app.core.config import settings


def generate_uuid() -> str:
    """Generate a UUID string"""
    return str(uuid.uuid4())


def calculate_success_rate(correct: int, total: int) -> int:
    """Calculate success rate percentage"""
    if total == 0:
        return 0
    return round(correct / total * 100)


def process_img_url(text: str | None, base_url: str | None = None) -> str | None:
    """Replace relative /api/v1/static/ URLs with absolute URLs

    Handles:
    - '/api/v1/static/uploads/a.png' -> 'http://host/api/v1/static/uploads/a.png'
    - '<img src="/api/v1/static/...">' -> '<img src="http://host/api/v1/static/...">'
    - Does NOT double-process already-absolute URLs
    """
    if not text or not isinstance(text, str):
        return text
    if not base_url:
        base_url = settings.server_host
    prefix = base_url.rstrip("/")
    # Only replace when /api/v1/static/ is NOT preceded by : or a word character
    # This prevents double-processing of already-absolute URLs like http://x.com/api/v1/static/...
    return re.sub(
        r'(?<![:\w])/api/v1/static/',
        f'{prefix}/api/v1/static/',
        text,
    )