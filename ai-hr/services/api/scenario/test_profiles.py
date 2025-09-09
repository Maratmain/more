#!/usr/bin/env python3
"""
Test script for role profiles and scenarios
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.api.scenario import (
    load_role_profiles, 
    get_profile_weights, 
    get_profile_threshold,
    load_scenario
)

def test_role_profiles():
    """Test role profiles loading and access"""
    print("🧪 Testing Role Profiles")
    print("=" * 50)
    
    # Test loading profiles
    profiles = load_role_profiles()
    if not profiles:
        print("❌ Failed to load role profiles")
        return False
    
    print(f"✅ Loaded role profiles: {profiles.get('version', 'unknown')}")
    
    # Test BA Anti-Fraud profile
    ba_weights = get_profile_weights('ba_anti_fraud')
    ba_threshold = get_profile_threshold('ba_anti_fraud')
    
    if ba_weights:
        print(f"✅ BA Anti-Fraud weights: {len(ba_weights)} blocks")
        print(f"   Threshold: {ba_threshold}")
        print(f"   Top weights: {sorted(ba_weights.items(), key=lambda x: x[1], reverse=True)[:3]}")
    else:
        print("❌ Failed to get BA Anti-Fraud weights")
        return False
    
    # Test IT DC Ops profile
    it_weights = get_profile_weights('it_dc_ops')
    it_threshold = get_profile_threshold('it_dc_ops')
    
    if it_weights:
        print(f"✅ IT DC Ops weights: {len(it_weights)} blocks")
        print(f"   Threshold: {it_threshold}")
        print(f"   Top weights: {sorted(it_weights.items(), key=lambda x: x[1], reverse=True)[:3]}")
    else:
        print("❌ Failed to get IT DC Ops weights")
        return False
    
    return True

def test_scenarios():
    """Test scenario loading"""
    print("\n🧪 Testing Scenarios")
    print("=" * 50)
    
    # Test BA scenario
    ba_scenario = load_scenario('ba_anti_fraud')
    if ba_scenario:
        print(f"✅ BA Anti-Fraud scenario: {len(ba_scenario.nodes)} nodes")
        print(f"   Start ID: {ba_scenario.start_id}")
        print(f"   Categories: {set(node.category for node in ba_scenario.nodes)}")
    else:
        print("❌ Failed to load BA Anti-Fraud scenario")
        return False
    
    # Test IT scenario
    it_scenario = load_scenario('it_dc_ops')
    if it_scenario:
        print(f"✅ IT DC Ops scenario: {len(it_scenario.nodes)} nodes")
        print(f"   Start ID: {it_scenario.start_id}")
        print(f"   Categories: {set(node.category for node in it_scenario.nodes)}")
    else:
        print("❌ Failed to load IT DC Ops scenario")
        return False
    
    return True

def test_integration():
    """Test integration between profiles and scenarios"""
    print("\n🧪 Testing Integration")
    print("=" * 50)
    
    # Get weights for BA profile
    ba_weights = get_profile_weights('ba_anti_fraud')
    ba_scenario = load_scenario('ba_anti_fraud')
    
    if ba_weights and ba_scenario:
        scenario_categories = set(node.category for node in ba_scenario.nodes)
        weight_categories = set(ba_weights.keys())
        
        print(f"✅ Scenario categories: {len(scenario_categories)}")
        print(f"✅ Weight categories: {len(weight_categories)}")
        
        missing_in_weights = scenario_categories - weight_categories
        missing_in_scenario = weight_categories - scenario_categories
        
        if missing_in_weights:
            print(f"⚠️  Categories in scenario but not in weights: {missing_in_weights}")
        
        if missing_in_scenario:
            print(f"⚠️  Categories in weights but not in scenario: {missing_in_scenario}")
        
        if not missing_in_weights and not missing_in_scenario:
            print("✅ Perfect alignment between scenario and weights!")
    
    return True

def main():
    """Main test function"""
    print("🚀 Role Profiles & Scenarios Test")
    print("=" * 50)
    
    success = True
    
    success &= test_role_profiles()
    success &= test_scenarios()
    success &= test_integration()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
