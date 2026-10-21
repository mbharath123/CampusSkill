import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-fallback-secret-change-in-prod")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_ENABLED = True

    # MySQL
    DB_HOST     = os.environ.get("DB_HOST", "localhost")
    DB_PORT     = int(os.environ.get("DB_PORT", 3306))
    DB_NAME     = os.environ.get("DB_NAME", "campusskill")
    DB_USER     = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
