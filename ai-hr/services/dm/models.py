from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Node(BaseModel):
    id: str
    category: str
    order: int
    question: str
    weight: float
    success_criteria: List[str] = []
    followups: List[str] = []
    next_if_fail: Optional[str] = None
    next_if_pass: Optional[str] = None

class ReplyIn(BaseModel):
    node: Node
    transcript: str = Field(..., description="ASR финальный текст")
    scores: Dict[str, float] = Field(default_factory=dict)  # блок -> [0..1]
    context: Dict[str, Any] = Field(default_factory=dict)
    role_profile: Optional[str] = Field(None, description="Role profile (ba_anti_fraud, it_dc_ops)")
    block_weights: Optional[Dict[str, float]] = Field(None, description="Block weights for scoring")

class ReplyOut(BaseModel):
    reply: str
    next_node_id: Optional[str] = None
    scoring_update: Dict[str, Any] = {}
    red_flags: List[str] = []
    delta_score: Optional[float] = Field(None, description="Score change for this response")
    confidence: Optional[float] = Field(None, description="Confidence in the response (0-1)")
    role_profile: Optional[str] = Field(None, description="Role profile used for response")
