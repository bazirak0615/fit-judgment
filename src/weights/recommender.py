import json
from src.llm import generate_json
from src.engine.schema import Weights


def recommend_weights(jd_structured: dict, weights: Weights, model: str = "qwen2.5:14b") -> dict:
    default_dict = {d.name: d.weight for d in weights.dimensions}
    return generate_json(
        "weight_recommend",
        {
            "jd_structured": json.dumps(jd_structured, ensure_ascii=False, indent=2),
            "default_weights": json.dumps(default_dict, ensure_ascii=False, indent=2),
        },
        model=model,
        temperature=0.3,
    )
