from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT_DIR / "backend"
DEFAULT_DATA_DIR = BACKEND_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "PaperLens AI API"
    app_env: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api"
    allowed_origins: list[str] = ["http://localhost:3000"]

    data_dir: Path = DEFAULT_DATA_DIR
    raw_pdfs_dir: Path = DEFAULT_DATA_DIR / "raw_pdfs"
    parsed_dir: Path = DEFAULT_DATA_DIR / "parsed"
    cache_dir: Path = DEFAULT_DATA_DIR / "cache"
    chroma_dir: Path = DEFAULT_DATA_DIR / "chroma"

    arxiv_base_url: str = "http://export.arxiv.org/api/query"
    openrouter_model: str = "openrouter/free"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L6-v2"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: Any) -> list[str] | Any:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    def ensure_directories(self) -> None:
        for path in (
            self.data_dir,
            self.raw_pdfs_dir,
            self.parsed_dir,
            self.cache_dir,
            self.chroma_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
