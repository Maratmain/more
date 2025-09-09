"""
BARS (Behaviorally Anchored Rating Scales) Scoring System

Implements weighted scoring with behavioral anchors:
- 0.0: No evidence / Poor performance
- 0.3: Below expectations / Limited evidence  
- 0.7: Meets expectations / Good evidence
- 1.0: Exceeds expectations / Excellent evidence

Supports weighted aggregation across questions and blocks.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class QAnswer:
    """Individual question answer with score and weight"""
    question_id: str
    block: str
    score: float   # 0 | 0.3 | 0.7 | 1 (or interpolation)
    weight: float  # importance of question (0..1)

@dataclass
class BlockWeights:
    """Block importance weights for overall scoring"""
    weights: Dict[str, float]  # block_name -> weight

# BARS behavioral anchors
BARS_ANCHORS = {
    0.0: "No evidence / Poor performance",
    0.3: "Below expectations / Limited evidence", 
    0.7: "Meets expectations / Good evidence",
    1.0: "Exceeds expectations / Excellent evidence"
}

def validate_score(score: float) -> float:
    """Validate and clamp score to valid BARS range"""
    if score < 0.0:
        return 0.0
    elif score > 1.0:
        return 1.0
    return score

def snap_to_anchor(score: float) -> float:
    """Snap score to nearest BARS anchor (0, 0.3, 0.7, 1.0)"""
    anchors = [0.0, 0.3, 0.7, 1.0]
    return min(anchors, key=lambda x: abs(x - score))

def score_block(answers: List[QAnswer], block: str) -> float:
    """
    Calculate weighted average score for a specific block.
    
    Args:
        answers: List of question answers
        block: Block name to score
        
    Returns:
        Weighted average score for the block (0..1)
    """
    subset = [a for a in answers if a.block == block]
    if not subset:
        return 0.0
    
    # Calculate weighted sum
    weighted_sum = sum(a.score * a.weight for a in subset)
    total_weight = sum(a.weight for a in subset)
    
    if total_weight == 0:
        return 0.0
    
    result = weighted_sum / total_weight
    return round(validate_score(result), 4)

def score_overall(block_scores: Dict[str, float], block_weights: Dict[str, float]) -> float:
    """
    Calculate overall weighted score across all blocks.
    
    Args:
        block_scores: Dict of block_name -> score
        block_weights: Dict of block_name -> weight
        
    Returns:
        Overall weighted score (0..1)
    """
    if not block_scores or not block_weights:
        return 0.0
    
    # Calculate weighted sum
    weighted_sum = sum(
        block_scores.get(block, 0.0) * weight 
        for block, weight in block_weights.items()
    )
    total_weight = sum(block_weights.values())
    
    if total_weight == 0:
        return 0.0
    
    result = weighted_sum / total_weight
    return round(validate_score(result), 4)

def calculate_match_score(
    candidate_scores: Dict[str, float],
    job_requirements: Dict[str, float],
    block_weights: Dict[str, float]
) -> float:
    """
    Calculate final match score between candidate and job requirements.
    
    Args:
        candidate_scores: Candidate's block scores
        job_requirements: Required minimum scores per block
        block_weights: Importance weights per block
        
    Returns:
        Match score (0..1) where 1.0 = perfect match
    """
    if not candidate_scores or not job_requirements or not block_weights:
        return 0.0
    
    match_scores = []
    total_weight = 0.0
    
    for block, weight in block_weights.items():
        candidate_score = candidate_scores.get(block, 0.0)
        required_score = job_requirements.get(block, 0.0)
        
        # Calculate match ratio for this block
        if required_score > 0:
            match_ratio = min(candidate_score / required_score, 1.0)
        else:
            match_ratio = 1.0 if candidate_score > 0 else 0.0
        
        match_scores.append(match_ratio * weight)
        total_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    result = sum(match_scores) / total_weight
    return round(validate_score(result), 4)

def get_bars_level(score: float) -> str:
    """Get BARS level description for a score"""
    if score >= 0.85:
        return BARS_ANCHORS[1.0]
    elif score >= 0.55:
        return BARS_ANCHORS[0.7]
    elif score >= 0.15:
        return BARS_ANCHORS[0.3]
    else:
        return BARS_ANCHORS[0.0]

def analyze_performance(answers: List[QAnswer], block_weights: Dict[str, float]) -> Dict:
    """
    Comprehensive performance analysis using BARS.
    
    Returns:
        Dict with block scores, overall score, and analysis
    """
    # Calculate block scores
    blocks = set(a.block for a in answers)
    block_scores = {block: score_block(answers, block) for block in blocks}
    
    # Calculate overall score
    overall_score = score_overall(block_scores, block_weights)
    
    # Analyze performance levels
    analysis = {
        "block_scores": block_scores,
        "overall_score": overall_score,
        "overall_level": get_bars_level(overall_score),
        "block_analysis": {
            block: {
                "score": score,
                "level": get_bars_level(score),
                "weight": block_weights.get(block, 0.0)
            }
            for block, score in block_scores.items()
        },
        "strengths": [
            block for block, score in block_scores.items() 
            if score >= 0.7
        ],
        "weaknesses": [
            block for block, score in block_scores.items() 
            if score < 0.3
        ]
    }
    
    return analysis
