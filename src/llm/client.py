import json
import os
import re
from datetime import datetime
from pathlib import Path
import ollama


DEFAULT_MODEL = "qwen2.5:14b"
PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"
DEBUG_DIR = Path(__file__).resolve().parents[2] / "data" / "llm_debug"
KEEP_ALIVE = "30m"  # 평가 도중 모델이 idle unload되지 않도록 충분히 길게


def get_backend() -> str:
    """LLM 백엔드 선택. 'ollama'(기본), 'mock', 'anthropic'(향후)."""
    return os.getenv("LLM_BACKEND", "ollama").lower()


class OllamaUnavailable(RuntimeError):
    """Ollama 서버가 응답하지 않을 때."""


class ModelNotInstalled(RuntimeError):
    """요청한 모델이 Ollama에 설치되어 있지 않을 때."""


def check_status(model: str | None = None) -> dict:
    """
    LLM 백엔드 상태 확인.
    반환: {"ok": bool, "models": [str], "error": str | None, "missing_model": bool, "backend": str}
    """
    backend = get_backend()
    if backend == "mock":
        return {
            "ok": True,
            "models": ["mock-llm"],
            "error": None,
            "missing_model": False,
            "backend": "mock",
        }

    try:
        resp = ollama.list()
    except Exception as e:
        return {"ok": False, "models": [], "error": f"Ollama 서버 연결 실패: {e}", "missing_model": False, "backend": "ollama"}

    raw_models = resp.get("models", []) if isinstance(resp, dict) else getattr(resp, "models", [])
    names: list[str] = []
    for m in raw_models:
        if isinstance(m, dict):
            n = m.get("name") or m.get("model")
        else:
            n = getattr(m, "name", None) or getattr(m, "model", None)
        if n:
            names.append(n)

    missing = bool(model) and model not in names and f"{model}:latest" not in names
    return {"ok": True, "models": names, "error": None, "missing_model": missing, "backend": "ollama"}


class OllamaClient:
    def __init__(self, model: str = DEFAULT_MODEL, host: str | None = None):
        self.model = model
        self.client = ollama.Client(host=host) if host else ollama

    def generate(self, prompt: str, system: str | None = None, temperature: float = 0.2) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            resp = self.client.chat(
                model=self.model,
                messages=messages,
                options={"temperature": temperature},
                keep_alive=KEEP_ALIVE,
            )
        except ollama.ResponseError as e:
            msg = str(e).lower()
            if "not found" in msg or "no such model" in msg or "try pulling" in msg:
                raise ModelNotInstalled(
                    f"모델 '{self.model}'이(가) 설치되지 않았습니다. "
                    f"터미널에서 다음 명령으로 설치하세요:\n  ollama pull {self.model}"
                ) from e
            raise
        except (ConnectionError, TimeoutError, OSError) as e:
            raise OllamaUnavailable(
                "Ollama 서버에 연결할 수 없습니다. 터미널에서 'ollama serve'를 실행하거나 "
                "Ollama 앱이 실행 중인지 확인하세요."
            ) from e
        return resp["message"]["content"]


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.txt"
    return path.read_text(encoding="utf-8")


def _save_debug_response(prompt_name: str, raw: str, error: str | None = None) -> Path:
    """LLM 응답을 디스크에 보존 — JSON 파싱 실패 시 디버깅용."""
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = "_ERR" if error else "_OK"
    path = DEBUG_DIR / f"{ts}_{prompt_name}{suffix}.txt"
    body = raw if not error else f"[ERROR: {error}]\n\n{raw}"
    path.write_text(body, encoding="utf-8")
    return path


def extract_json(text: str) -> dict:
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        candidate = fence.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"JSON 객체를 찾을 수 없습니다: {text[:200]}")
        candidate = text[start : end + 1]
    return json.loads(candidate)


def generate_json(
    prompt_name: str,
    variables: dict,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.2,
) -> dict:
    backend = get_backend()
    if backend == "mock":
        from .mock_backend import mock_generate_json
        return mock_generate_json(prompt_name, variables, model=model, temperature=temperature)

    # Default: ollama
    template = load_prompt(prompt_name)
    prompt = template.format(**variables)
    client = OllamaClient(model=model)
    raw = client.generate(prompt, temperature=temperature)
    try:
        return extract_json(raw)
    except (ValueError, json.JSONDecodeError) as e:
        path = _save_debug_response(prompt_name, raw, error=str(e))
        raise ValueError(
            f"LLM 응답 JSON 파싱 실패. 원본 응답이 저장됐습니다: {path.name}\n"
            f"원본 응답 길이: {len(raw):,}자\n"
            f"파싱 에러: {e}"
        ) from e
