"""
Helper utilities
"""
import uuid


def generate_uuid() -> str:
    """Generate a UUID string"""
    return str(uuid.uuid4())


def calculate_success_rate(correct: int, total: int) -> int:
    """Calculate success rate percentage"""
    if total == 0:
        return 0
    return round(correct / total * 100)