import json
from pathlib import Path

MAX_CANDIDATES_PER_JSON = 100


def load_json_candidates(file_path: str | Path) -> list[dict]:
    """
    JSON 파일에서 후보자 1명 또는 여러 명을 로드.

    지원 형식:
    1) 단일 객체: {"name": "...", "resume": "..."} 또는 {"name": "...", "...": ...}
    2) 배열: [{...}, {...}, ...]
    3) 래핑 객체: {"candidates": [{...}, ...]}

    각 후보자는 다음 필드 중 하나로 본문 텍스트 제공:
    - "resume" / "resume_text" / "text" / "content" : 평문 이력서
    - 없으면 객체 전체를 JSON 문자열로 직렬화해서 사용

    "name" / "label" / "id"가 있으면 후보자 식별자로 사용.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "candidates" in data:
        items = data["candidates"]
    elif isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = [data]
    else:
        raise ValueError("JSON 형식이 올바르지 않습니다 (객체 또는 배열이어야 함).")

    if not isinstance(items, list):
        raise ValueError("'candidates' 필드는 배열이어야 합니다.")

    if len(items) > MAX_CANDIDATES_PER_JSON:
        raise ValueError(
            f"한 JSON 파일에 후보자가 {len(items)}명입니다. "
            f"최대 {MAX_CANDIDATES_PER_JSON}명까지 허용됩니다."
        )

    out = []
    for i, item in enumerate(items, 1):
        if not isinstance(item, dict):
            out.append({"label": f"candidate_{i}", "resume_text": str(item)})
            continue

        label = (
            item.get("name")
            or item.get("label")
            or item.get("id")
            or f"candidate_{i}"
        )

        text = (
            item.get("resume")
            or item.get("resume_text")
            or item.get("text")
            or item.get("content")
        )
        if not text:
            text = json.dumps(item, ensure_ascii=False, indent=2)

        out.append({"label": str(label), "resume_text": str(text)})

    return out
