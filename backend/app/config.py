import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    APP_NAME: str = "CodePilot AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Base storage directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    REPOS_DIR: Path = DATA_DIR / "repos"
    SANDBOX_DIR: Path = DATA_DIR / "sandbox"
    BENCHMARKS_DIR: Path = BASE_DIR.parent / "benchmarks"

    # Database
    DATABASE_URL: str = f"sqlite:///{(DATA_DIR / 'codepilot.db').as_posix()}"

    # LLM Settings
    LLM_PROVIDER: str = "mock"  # "mock" or "anthropic"
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.2

    # Upload & Repository Security Limits
    MAX_UPLOAD_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB
    MAX_FILE_COUNT: int = 2500
    MAX_FILE_SIZE_BYTES: int = 2 * 1024 * 1024  # 2 MB per file for inspection
    MAX_ARCHIVE_TOTAL_EXTRACT_SIZE: int = 100 * 1024 * 1024  # 100 MB extraction ceiling
    
    # Execution & Sandboxing Security
    EXECUTION_TIMEOUT_SECONDS: int = 30
    ENABLE_ISOLATED_VERIFICATION: bool = True
    ALLOWED_COMMAND_PREFIXES: List[str] = [
        "pytest",
        "python -m pytest",
        "python -m unittest",
        "npm test",
        "npx jest",
        "npm run test"
    ]

    # CORS
    CORS_ORIGINS: List[str] = ["*"]



settings = Settings()

# Ensure required directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.REPOS_DIR.mkdir(parents=True, exist_ok=True)
settings.SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
