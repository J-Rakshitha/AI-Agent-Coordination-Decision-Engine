"""
Central configuration for the AI Agent Coordination & Decision Engine.
Loads values from environment variables / .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AI Agent Coordination & Decision Engine"
    ENV: str = "development"
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./coordination_engine.db"

    # LLM (Hybrid AI strategy)
    GEMINI_API_KEY: str = ""
    LLM_PROVIDER: str = "gemini"
    LLM_ENABLED: bool = True
    LLM_TIMEOUT_SECONDS: int = 6

    # CORS
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # Synthetic data generator toggle (safe demo mode)
    SYNTHETIC_DATA_ENABLED: bool = True

    # Real GitHub Integration (Phase A — replaces simulated dev-collab data)
    GITHUB_TOKEN: str = ""
    GITHUB_REPO_OWNER: str = "J-Rakshitha"
    GITHUB_REPO_NAME: str = "dev-collab-test-repo"

    # Phase B — Real Server Monitoring (background HTTP probes)
    MONITORING_ENABLED: bool = True
    MONITOR_INTERVAL_SECONDS: int = 30
    MONITOR_BACKEND_NAME: str = "coordination-engine-backend"
    MONITOR_BACKEND_URL: str = "http://127.0.0.1:8000/api/system/health"
    MONITOR_EXTERNAL_NAME: str = "github-external-api"
    MONITOR_EXTERNAL_URL: str = "https://api.github.com"

    # Phase C — Multi-user Login (JWT)
    AUTH_SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Singleton settings instance used across the app
settings = Settings()

_PLACEHOLDER_API_KEYS = {
    "",
    "your_gemini_api_key_here",
    "your-gemini-api-key-here",
    "changeme",
}


def is_llm_key_valid() -> bool:
    """True only when a real (non-placeholder) Gemini key is configured."""
    key = (settings.GEMINI_API_KEY or "").strip()
    return key not in _PLACEHOLDER_API_KEYS and len(key) > 10
