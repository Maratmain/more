from .schema import QNode, Scenario

def next_node(current: QNode, score: float, scen: Scenario) -> str | None:
    thr = scen.policy.get("drill_threshold", 0.7)
    return current.next_if_fail if score < thr else current.next_if_pass
