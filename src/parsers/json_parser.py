import json
from pathlib import Path


def parse_json(file_path: str | Path) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return json.dumps(data, ensure_ascii=False, indent=2)
