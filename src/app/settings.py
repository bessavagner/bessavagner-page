import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
CONTENT_DIR = PROJECT_ROOT / "content"
CSS_FILE = STATIC_DIR / "css" / "output.css"

SITE_URL = os.getenv("SITE_URL", "https://bessavagner.com").rstrip("/")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://0.0.0.0:8080").split(",")
    if origin.strip()
]
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
DEBUG = bool(int(os.getenv("DEBUG", "1")))
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "465"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "change-me@example.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "change-me")
EMAIL_USE_TLS = bool(int(os.getenv("EMAIL_USE_TLS", "1")))
EMAIL_DEFAULT_SENDER = os.getenv("EMAIL_DEFAULT_SENDER", "change-me@example.com")
