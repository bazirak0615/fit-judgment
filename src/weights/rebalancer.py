from src.engine.schema import Weights, Category


def rebalance(weights: Weights, changed_name: str, new_value: float) -> Weights:
    target = next((d for d in weights.dimensions if d.name == changed_name), None)
    if target is None:
        raise ValueError(f"차원을 찾을 수 없습니다: {changed_name}")

    new_value = max(0.0, min(0.5, new_value))
    delta = new_value - target.weight
    target.weight = new_value

    siblings = [d for d in weights.dimensions if d.name != changed_name and d.category == target.category]
    sibling_total = sum(d.weight for d in siblings)
    if sibling_total <= 0:
        if siblings:
            even = max(0.0, -delta / len(siblings))
            for d in siblings:
                d.weight = even
        return weights

    for d in siblings:
        share = d.weight / sibling_total
        d.weight = max(0.0, d.weight - delta * share)

    drift = 1.0 - sum(d.weight for d in weights.dimensions)
    if abs(drift) > 1e-9 and siblings:
        siblings[0].weight = max(0.0, siblings[0].weight + drift)

    return weights
