# Модуль управления сценариями интервью
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from .schema import QNode, Scenario
from .selector import next_node
from .generator import load_scenario, generate_fallback_scenario

def load_role_profiles() -> Dict[str, Any] | None:
    """Загрузка профилей ролей из YAML"""
    try:
        profiles_file = Path(__file__).parent / "role_profiles.yaml"
        if not profiles_file.exists():
            return None
        with open(profiles_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception:
        return None

def get_profile_weights(profile_id: str) -> Dict[str, float] | None:
    """Получение весов блоков для профиля"""
    profiles = load_role_profiles()
    if not profiles or 'profiles' not in profiles:
        return None
    profile = profiles['profiles'].get(profile_id)
    return profile.get('block_weights', {}) if profile else None

def get_profile_threshold(profile_id: str) -> float:
    """Получение порога углубления для профиля"""
    profiles = load_role_profiles()
    if not profiles or 'profiles' not in profiles:
        return 0.7
    profile = profiles['profiles'].get(profile_id)
    return profile.get('drill_threshold', 0.7) if profile else 0.7

__all__ = [
    "QNode",
    "Scenario", 
    "next_node",
    "load_scenario",
    "generate_fallback_scenario",
    "load_role_profiles",
    "get_profile_weights",
    "get_profile_threshold"
]
