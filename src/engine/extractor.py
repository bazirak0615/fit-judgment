from src.llm import generate_json


def extract_jd(jd_text: str, model: str = "qwen2.5:14b") -> dict:
    return generate_json("jd_extract", {"jd_text": jd_text}, model=model)


def extract_candidate(resume_text: str, model: str = "qwen2.5:14b") -> dict:
    return generate_json("candidate_extract", {"resume_text": resume_text}, model=model)
