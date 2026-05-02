from pathlib import Path


def parse_text(file_path: str | Path) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
