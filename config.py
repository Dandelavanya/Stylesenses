# StyleAI Configuration
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Upload settings
UPLOAD_FOLDER = BASE_DIR / "uploads"
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# Groq API
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS = 1200
TEMPERATURE = 0.7
TIMEOUT = 90

# Skin tone categories
SKIN_TONES = ("Fair", "Medium", "Olive", "Deep")
