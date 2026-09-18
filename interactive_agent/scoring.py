"""Paired exact-choice evaluation with explicit failure denominators."""
from graphrag.eval.mirage_benchmark import _mcnemar_exact_p, _wilson_interval


def compare(records, baseline, candidate):
    if baseline == candidate:
        raise ValueError("Select two distinct arms")
    by_arm = {baseline: {}, candidate: {}}
    for record in records:
        arm = record["arm"]
        if arm not in by_arm:
            continue
        case_id = record["case_id"]
        if case_id in by_arm[arm]:
            raise ValueError(f"Duplicate case/arm: {case_id}/{arm}")
        if type(record.get("correct")) is not bool or type(record.get("valid")) is not bool:
            raise ValueError("correct and valid must be explicit booleans")
        by_arm[arm][case_id] = record
    ids = set(by_arm[baseline])
    if not ids or ids != set(by_arm[candidate]):
        raise ValueError("Paired comparison requires identical, nonempty case sets")
    n = len(ids)
    arms = {}
    for name, cases in by_arm.items():
        correct = sum(r["correct"] for r in cases.values())
        valid = sum(r["valid"] for r in cases.values())
        valid_correct = sum(r["correct"] and r["valid"] for r in cases.values())
        arms[name] = {
            "n": n, "correct": correct, "accuracy": correct / n,
            "wilson_95ci": _wilson_interval(correct, n),
            "valid_rate": valid / n,
            "valid_and_correct_rate": valid_correct / n,
            "selective_accuracy": valid_correct / valid if valid else None,
        }
    wins = sum(by_arm[candidate][i]["correct"] and not by_arm[baseline][i]["correct"] for i in ids)
    losses = sum(by_arm[baseline][i]["correct"] and not by_arm[candidate][i]["correct"] for i in ids)
    return {"arms": arms, "candidate_wins": wins, "candidate_losses": losses,
            "ties": n - wins - losses,
            "mcnemar_exact_p": _mcnemar_exact_p(wins, losses)}
