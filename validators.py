"""Image upload validation for StyleAI."""
import os
from typing import Tuple

from config import ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    if not filename or "." not in filename:
        return False
    return filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_upload(file) -> Tuple[bool, str]:
    """
    Validate uploaded file. Returns (is_valid, error_message).
    Empty error_message means valid.
    """
    if file is None or not file.filename:
        return False, "No file selected."
    if not allowed_file(file.filename):
        return False, f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}."
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_CONTENT_LENGTH:
        return False, f"File too large. Maximum size is {MAX_CONTENT_LENGTH // (1024*1024)}MB."
    return True, ""
