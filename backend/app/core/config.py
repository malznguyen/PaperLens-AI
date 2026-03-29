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
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openrouter/free"
    openrouter_timeout_seconds: float = 45.0
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    retrieval_top_k_default: int = 6
    retrieval_top_k_max: int = 12
    compare_top_k_per_paper: int = 2
    synthesis_top_k: int = 6
    compare_max_papers: int = 5
    enable_metrics_collection: bool = True
    compare_generation_temperature: float = 0.1
    synthesis_generation_temperature: float = 0.1
    reranking_enabled: bool = True
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    chunk_size_words: int = 850
    chunk_overlap_words: int = 120
    chroma_collection_name: str = "paper_chunks"
    generation_chunk_char_limit: int = 1800
    generation_context_char_limit: int = 12000

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: Any) -> list[str] | Any:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("openrouter_api_key", mode="before")
    @classmethod
    def parse_openrouter_api_key(cls, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    @field_validator("chunk_size_words")
    @classmethod
    def validate_chunk_size_words(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("chunk_size_words must be greater than zero.")
        return value

    @field_validator("chunk_overlap_words")
    @classmethod
    def validate_chunk_overlap_words(cls, value: int, info) -> int:
        chunk_size = info.data.get("chunk_size_words", 1)
        if value < 0:
            raise ValueError("chunk_overlap_words must not be negative.")
        if value >= chunk_size:
            raise ValueError("chunk_overlap_words must be smaller than chunk_size_words.")
        return value

    @field_validator("openrouter_timeout_seconds")
    @classmethod
    def validate_openrouter_timeout_seconds(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("openrouter_timeout_seconds must be greater than zero.")
        return value

    @field_validator("retrieval_top_k_default")
    @classmethod
    def validate_retrieval_top_k_default(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("retrieval_top_k_default must be greater than zero.")
        return value

    @field_validator("retrieval_top_k_max")
    @classmethod
    def validate_retrieval_top_k_max(cls, value: int, info) -> int:
        default_top_k = info.data.get("retrieval_top_k_default", 1)
        if value <= 0:
            raise ValueError("retrieval_top_k_max must be greater than zero.")
        if value < default_top_k:
            raise ValueError(
                "retrieval_top_k_max must be greater than or equal to retrieval_top_k_default."
            )
        return value

    @field_validator("compare_top_k_per_paper", "synthesis_top_k", "compare_max_papers")
    @classmethod
    def validate_phase_six_limits(cls, value: int, info) -> int:
        if value <= 0:
            raise ValueError(f"{info.field_name} must be greater than zero.")
        return value

    @field_validator("compare_max_papers")
    @classmethod
    def validate_compare_max_papers(cls, value: int) -> int:
        if value < 2:
            raise ValueError("compare_max_papers must be at least 2.")
        if value > 5:
            raise ValueError("compare_max_papers must not exceed 5.")
        return value

    @field_validator("compare_generation_temperature", "synthesis_generation_temperature")
    @classmethod
    def validate_generation_temperatures(cls, value: float, info) -> float:
        if value < 0 or value > 1:
            raise ValueError(f"{info.field_name} must be between 0 and 1.")
        return value

    @field_validator("generation_chunk_char_limit", "generation_context_char_limit")
    @classmethod
    def validate_generation_char_limits(cls, value: int, info) -> int:
        if value <= 0:
            raise ValueError(f"{info.field_name} must be greater than zero.")
        return value

    @property
    def indexing_cache_dir(self) -> Path:
        return self.cache_dir / "indexing"

    def ensure_directories(self) -> None:
        for path in (
            self.data_dir,
            self.raw_pdfs_dir,
            self.parsed_dir,
            self.cache_dir,
            self.indexing_cache_dir,
            self.chroma_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
