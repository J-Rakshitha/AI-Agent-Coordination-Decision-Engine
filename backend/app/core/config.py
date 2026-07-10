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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Singleton settings instance used across the app
settings = Settings()
