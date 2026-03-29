from __future__ import annotations

import re
from pathlib import Path

from app.core.config import ROOT_DIR

UNSAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def build_storage_stem(paper_id: str, title: str | None = None) -> str:
    for candidate in (paper_id, title or ""):
        normalized = UNSAFE_FILENAME_RE.sub(
            "-",
            candidate.strip().replace("/", "-").replace("\\", "-"),
        ).strip("._-")
        if normalized:
            return normalized.lower()

    return "paper"


def repo_relative_path(path: Path) -> str:
    resolved_path = path.resolve()

    try:
        return resolved_path.relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return resolved_path.as_posix()


def write_bytes_file(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
