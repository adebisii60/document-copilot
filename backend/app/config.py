"""
Application configuration loaded from environment variables.

This is the single source of truth for all settings. Use `settings` singleton
throughout the app instead of calling os.getenv() or os.environ directly.

Fails fast on startup if required config is missing.
"""

try:
    # Some editors/linters may flag this import as unresolved in environments
    # where pydantic-settings isn't installed. Silence static analyzers while
    # keeping the runtime import intact.
    from pydantic_settings import BaseSettings  # type: ignore
except Exception:  # pragma: no cover - fallback for editors/CI without pydantic_settings installed
    # Minimal fallback to allow static analysis / editors to work when
    # pydantic-settings is not available. At runtime, install it to get full behavior.
    class BaseSettings:  # type: ignore
        class Config:  # type: ignore
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False

        def __init__(self, *args, **kwargs):
            # no-op: real BaseSettings will populate fields from env
            return None


class Settings(BaseSettings):
    """Application settings loaded from .env or environment."""

    # --- Supabase (Auth + API) ---
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # --- Postgres (Alembic + direct DB access) ---
    database_url: str
    database_pooler_url: str | None = None
    database_migration_url: str | None = None

    # --- OpenAI (LLM & embeddings) ---
    openai_api_key: str
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536

    # --- Server ---
    allowed_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance.
# Import this in app code instead of creating new Settings() or reading os.getenv() directly.
settings = Settings()
