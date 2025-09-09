from pydantic import BaseModel
from typing import List, Dict, Optional

class QNode(BaseModel):
    id: str
    category: str
    order: int  # 1..4
    question: str
    weight: float
    success_criteria: List[str] = []
    followups: List[str] = []
    next_if_fail: Optional[str] = None
    next_if_pass: Optional[str] = None

class Scenario(BaseModel):
    schema_version: str = "0.1"
    policy: Dict[str, float] = {"drill_threshold": 0.7}
    nodes: List[QNode]
    start_id: str
