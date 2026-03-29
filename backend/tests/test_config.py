from app.core.config import ROOT_DIR, Settings


def test_arxiv_base_url_defaults_to_https(monkeypatch) -> None:
    monkeypatch.delenv("ARXIV_BASE_URL", raising=False)

    settings = Settings(_env_file=None)

    assert settings.arxiv_base_url == "https://export.arxiv.org/api/query"


def test_allowed_origins_accepts_plain_env_string(monkeypatch) -> None:
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:3000")

    settings = Settings(_env_file=None)

    assert settings.allowed_origins == ["http://localhost:3000"]


def test_allowed_origins_accepts_comma_separated_env_string(monkeypatch) -> None:
    monkeypatch.setenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000, http://127.0.0.1:3000",
    )

    settings = Settings(_env_file=None)

    assert settings.allowed_origins == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def test_allowed_origins_accepts_json_env_array(monkeypatch) -> None:
    monkeypatch.setenv(
        "ALLOWED_ORIGINS",
        '["http://localhost:3000", "http://127.0.0.1:3000"]',
    )

    settings = Settings(_env_file=None)

    assert settings.allowed_origins == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def test_relative_runtime_paths_resolve_from_repo_root(monkeypatch) -> None:
    monkeypatch.chdir(ROOT_DIR / "backend")
    monkeypatch.setenv("DATA_DIR", "backend/data")
    monkeypatch.setenv("CHROMA_DIR", "backend/data/chroma")

    settings = Settings(_env_file=None)

    assert settings.data_dir == ROOT_DIR / "backend" / "data"
    assert settings.raw_pdfs_dir == ROOT_DIR / "backend" / "data" / "raw_pdfs"
    assert settings.parsed_dir == ROOT_DIR / "backend" / "data" / "parsed"
    assert settings.cache_dir == ROOT_DIR / "backend" / "data" / "cache"
    assert settings.chroma_dir == ROOT_DIR / "backend" / "data" / "chroma"
