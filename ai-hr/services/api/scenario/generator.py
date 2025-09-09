"""
Fallback generator for creating 3-node chains for any category
Ensures demo doesn't break if main scenario loading fails
"""

from .schema import QNode, Scenario

def generate_fallback_scenario(category: str) -> Scenario:
    """Generate a simple 3-node chain for any category"""
    
    nodes = [
        QNode(
            id=f"{category}_l1_intro",
            category=category,
            order=1,
            question=f"Расскажите о вашем опыте работы с {category}",
            weight=1.0,
            success_criteria=["опыт", "проекты", "навыки"],
            followups=["Какие проекты вы делали?"],
            next_if_fail=f"{category}_l2_basics",
            next_if_pass=f"{category}_l3_advanced"
        ),
        QNode(
            id=f"{category}_l2_basics",
            category=category,
            order=2,
            question=f"Объясните основные концепции {category}",
            weight=0.8,
            success_criteria=["основы", "концепции", "принципы"],
            followups=["Что самое важное?"],
            next_if_fail=f"{category}_l3_advanced",
            next_if_pass=f"{category}_l3_advanced"
        ),
        QNode(
            id=f"{category}_l3_advanced",
            category=category,
            order=3,
            question=f"Как вы решали сложные задачи в {category}?",
            weight=0.9,
            success_criteria=["сложные задачи", "решения", "оптимизация"],
            followups=["Приведите примеры"],
            next_if_fail=None,
            next_if_pass=None
        )
    ]
    
    return Scenario(
        schema_version="0.1",
        policy={"drill_threshold": 0.7},
        nodes=nodes,
        start_id=f"{category}_l1_intro"
    )

def load_scenario(category: str) -> Scenario:
    """Load scenario with fallback to generator"""
    try:
        # Try to load from examples
        import json
        import os
        
        examples_dir = os.path.join(os.path.dirname(__file__), "examples")
        scenario_file = os.path.join(examples_dir, f"{category}.json")
        
        if os.path.exists(scenario_file):
            with open(scenario_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Scenario(**data)
        else:
            # Fallback to generator
            return generate_fallback_scenario(category)
            
    except Exception as e:
        print(f"Failed to load scenario for {category}: {e}")
        # Ultimate fallback
        return generate_fallback_scenario(category)
