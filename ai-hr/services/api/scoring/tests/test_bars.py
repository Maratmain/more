"""
Comprehensive tests for BARS scoring system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from services.api.scoring.bars import (
    QAnswer, score_block, score_overall, calculate_match_score,
    validate_score, snap_to_anchor, get_bars_level, analyze_performance
)

def test_block_weighted_mean():
    """Test weighted average calculation for a block"""
    data = [
        QAnswer("q1", "Django", 1.0, 0.5),
        QAnswer("q2", "Django", 0.7, 0.5),
    ]
    result = score_block(data, "Django")
    expected = (1.0 * 0.5 + 0.7 * 0.5) / (0.5 + 0.5)  # 0.85
    assert abs(result - expected) < 1e-6, f"Expected {expected}, got {result}"

def test_block_empty():
    """Test scoring empty block"""
    data = [
        QAnswer("q1", "Django", 1.0, 0.5),
    ]
    result = score_block(data, "React")
    assert result == 0.0, f"Expected 0.0 for empty block, got {result}"

def test_block_zero_weights():
    """Test scoring with zero weights"""
    data = [
        QAnswer("q1", "Django", 1.0, 0.0),
        QAnswer("q2", "Django", 0.7, 0.0),
    ]
    result = score_block(data, "Django")
    assert result == 0.0, f"Expected 0.0 for zero weights, got {result}"

def test_overall():
    """Test overall weighted scoring"""
    block_scores = {"Django": 0.85, "DB": 0.6}
    block_weights = {"Django": 0.95, "DB": 0.85}
    # (0.85*0.95 + 0.6*0.85) / (0.95+0.85) = 1.3475 / 1.8 = 0.7486
    result = score_overall(block_scores, block_weights)
    expected = (0.85 * 0.95 + 0.6 * 0.85) / (0.95 + 0.85)
    assert abs(result - expected) < 1e-3, f"Expected {expected}, got {result}"

def test_overall_empty():
    """Test overall scoring with empty data"""
    result = score_overall({}, {})
    assert result == 0.0, f"Expected 0.0 for empty data, got {result}"

def test_match_score():
    """Test candidate-job match calculation"""
    candidate_scores = {"Django": 0.8, "DB": 0.6, "React": 0.9}
    job_requirements = {"Django": 0.7, "DB": 0.5, "React": 0.8}
    block_weights = {"Django": 0.4, "DB": 0.3, "React": 0.3}
    
    result = calculate_match_score(candidate_scores, job_requirements, block_weights)
    
    # Django: 0.8/0.7 = 1.0 (capped), DB: 0.6/0.5 = 1.0 (capped), React: 0.9/0.8 = 1.0 (capped)
    # All ratios are 1.0, so result should be 1.0
    assert abs(result - 1.0) < 1e-6, f"Expected 1.0 for perfect match, got {result}"

def test_match_score_partial():
    """Test partial match calculation"""
    candidate_scores = {"Django": 0.5, "DB": 0.3}
    job_requirements = {"Django": 0.7, "DB": 0.5}
    block_weights = {"Django": 0.6, "DB": 0.4}
    
    result = calculate_match_score(candidate_scores, job_requirements, block_weights)
    
    # Django: 0.5/0.7 = 0.714, DB: 0.3/0.5 = 0.6
    # Weighted: (0.714*0.6 + 0.6*0.4) / (0.6+0.4) = 0.6684
    expected = (0.714 * 0.6 + 0.6 * 0.4) / 1.0
    assert abs(result - expected) < 1e-3, f"Expected ~{expected}, got {result}"

def test_validate_score():
    """Test score validation and clamping"""
    assert validate_score(-0.1) == 0.0, "Negative score should be clamped to 0.0"
    assert validate_score(1.1) == 1.0, "Score > 1.0 should be clamped to 1.0"
    assert validate_score(0.5) == 0.5, "Valid score should remain unchanged"

def test_snap_to_anchor():
    """Test snapping to BARS anchors"""
    assert snap_to_anchor(0.1) == 0.0, "0.1 should snap to 0.0"
    assert snap_to_anchor(0.2) == 0.3, "0.2 should snap to 0.3"
    assert snap_to_anchor(0.5) == 0.7, "0.5 should snap to 0.7"
    assert snap_to_anchor(0.8) == 0.7, "0.8 should snap to 0.7"
    assert snap_to_anchor(0.9) == 1.0, "0.9 should snap to 1.0"

def test_get_bars_level():
    """Test BARS level descriptions"""
    assert "Excellent" in get_bars_level(0.9), "High score should indicate excellent"
    assert "Meets" in get_bars_level(0.7), "Medium score should indicate meets expectations"
    assert "Below" in get_bars_level(0.3), "Low score should indicate below expectations"
    assert "Poor" in get_bars_level(0.1), "Very low score should indicate poor"

def test_analyze_performance():
    """Test comprehensive performance analysis"""
    answers = [
        QAnswer("q1", "Django", 1.0, 0.5),
        QAnswer("q2", "Django", 0.7, 0.5),
        QAnswer("q3", "React", 0.3, 0.8),
        QAnswer("q4", "React", 0.7, 0.2),
    ]
    block_weights = {"Django": 0.6, "React": 0.4}
    
    analysis = analyze_performance(answers, block_weights)
    
    # Check structure
    assert "block_scores" in analysis
    assert "overall_score" in analysis
    assert "overall_level" in analysis
    assert "block_analysis" in analysis
    assert "strengths" in analysis
    assert "weaknesses" in analysis
    
    # Check Django block score
    django_score = analysis["block_scores"]["Django"]
    expected_django = (1.0 * 0.5 + 0.7 * 0.5) / 1.0  # 0.85
    assert abs(django_score - expected_django) < 1e-6
    
    # Check React block score  
    react_score = analysis["block_scores"]["React"]
    expected_react = (0.3 * 0.8 + 0.7 * 0.2) / 1.0  # 0.38
    assert abs(react_score - expected_react) < 1e-6
    
    # Check strengths and weaknesses
    assert "Django" in analysis["strengths"], "Django should be a strength"
    # React score is 0.38, which is >= 0.3, so it's not in weaknesses
    assert "React" not in analysis["weaknesses"], "React score 0.38 should not be in weaknesses"

def test_edge_cases():
    """Test edge cases and error conditions"""
    # Single answer
    single_answer = [QAnswer("q1", "Test", 0.7, 1.0)]
    result = score_block(single_answer, "Test")
    assert result == 0.7, f"Single answer should return its score, got {result}"
    
    # Zero score
    zero_score = [QAnswer("q1", "Test", 0.0, 1.0)]
    result = score_block(zero_score, "Test")
    assert result == 0.0, f"Zero score should return 0.0, got {result}"
    
    # Very small weights
    small_weights = [QAnswer("q1", "Test", 1.0, 0.001)]
    result = score_block(small_weights, "Test")
    assert result == 1.0, f"Small weight should still work, got {result}"

def run_all_tests():
    """Run all tests and report results"""
    tests = [
        test_block_weighted_mean,
        test_block_empty,
        test_block_zero_weights,
        test_overall,
        test_overall_empty,
        test_match_score,
        test_match_score_partial,
        test_validate_score,
        test_snap_to_anchor,
        test_get_bars_level,
        test_analyze_performance,
        test_edge_cases
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return failed == 0

if __name__ == "__main__":
    run_all_tests()
