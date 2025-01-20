import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
CSS_FILE = STATIC_DIR / "css" / "output.css"

ALLOWED_ORIGINS = os.getenv(
        'ALLOWED_ORIGINS', 'http://0.0.0.0/8080'
    ).split(',')
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
DEBUG = bool(int(os.getenv("DEBUG", "1")))
