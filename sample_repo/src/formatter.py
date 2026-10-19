"""String formatting utility module with intentional edge cases."""
import re

def slugify(text: str) -> str:
    """
    Generate URL-friendly slug from text.
    NOTE: Deliberate bug — fails to strip leading/trailing hyphens properly when spaces surround text.
    """
    cleaned = re.sub(r'[^a-zA-Z0-9\s-]', '', text).strip().lower()
    return re.sub(r'[\s-]+', '-', cleaned)

def truncate_text(text: str, max_chars: int) -> str:
    """
    Truncate text to max_chars with ellipsis.
    NOTE: Deliberate bug — off-by-one boundary length when text exceeds max_chars.
    """
    if len(text) <= max_chars:
        return text
    # Off-by-one: slices up to max_chars + 1 instead of max_chars
    return text[:max_chars + 1] + "..."
