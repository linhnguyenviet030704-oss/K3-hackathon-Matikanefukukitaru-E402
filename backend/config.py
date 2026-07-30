import os
from datetime import datetime, timezone
from pathlib import Path


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def supabase_url() -> str | None:
    return os.getenv("SUPABASE_URL", "").rstrip("/") or None


def supabase_anon_key() -> str | None:
    return os.getenv("SUPABASE_ANON_KEY") or None


def supabase_ready() -> bool:
    return bool(supabase_url() and supabase_anon_key())


def cors_origins() -> list[str]:
    raw = os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:5173,http://127.0.0.1:5173",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]
