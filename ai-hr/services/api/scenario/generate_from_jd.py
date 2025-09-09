#!/usr/bin/env python3
"""
Utility to generate interview scenarios from Job Descriptions using LLM Gateway

This script reads a JD text file and generates a structured interview scenario
using the LLM Gateway service with appropriate prompt templates.
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
LLM_GW_URL = os.getenv("LLM_GW_URL", "http://localhost:8008")
PROMPTS_DIR = Path(__file__).parent.parent.parent / "llm-gw" / "prompts"
EXAMPLES_DIR = Path(__file__).parent / "examples"

class JDScenarioGenerator:
    """Generate interview scenarios from Job Descriptions"""
    
    def __init__(self, llm_gw_url: str = LLM_GW_URL):
        self.llm_gw_url = llm_gw_url
        self.prompts_dir = PROMPTS_DIR
        self.examples_dir = EXAMPLES_DIR
        
        # Ensure examples directory exists
        self.examples_dir.mkdir(exist_ok=True)
    
    def load_prompt_template(self, role_type: str) -> str:
        """Load prompt template for the specified role type"""
        template_file = self.prompts_dir / f"jd_to_questions_{role_type}.txt"
        
        if not template_file.exists():
            raise FileNotFoundError(f"Prompt template not found: {template_file}")
        
        with open(template_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def load_jd_content(self, jd_file: str) -> str:
        """Load Job Description content from file"""
        jd_path = Path(jd_file)
        
        if not jd_path.exists():
            raise FileNotFoundError(f"JD file not found: {jd_path}")
        
        with open(jd_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def call_llm_gateway(self, system_prompt: str, user_prompt: str, model: str = "env_default") -> Dict[str, Any]:
        """Call LLM Gateway service to generate scenario"""
        payload = {
            "system": system_prompt,
            "prompt": user_prompt,
            "model": model,
            "stream": False,
            "max_tokens": 4000,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                f"{self.llm_gw_url}/generate",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM Gateway request failed: {e}")
            raise
    
    def parse_llm_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response and extract JSON scenario"""
        content = response.get("content", "")
        
        # Try to extract JSON from the response
        # Look for JSON block between ```json and ```
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end != -1:
                json_str = content[start:end].strip()
            else:
                json_str = content[start:].strip()
        else:
            # Try to find JSON object in the response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                json_str = content[start:end]
            else:
                json_str = content
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            logger.error(f"Response content: {content}")
            raise
    
    def validate_scenario(self, scenario: Dict[str, Any]) -> bool:
        """Validate generated scenario structure"""
        required_fields = ["id", "role_profile", "policy", "nodes", "start_id"]
        
        for field in required_fields:
            if field not in scenario:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate nodes structure
        if not isinstance(scenario["nodes"], list):
            logger.error("Nodes must be a list")
            return False
        
        for i, node in enumerate(scenario["nodes"]):
            node_required_fields = ["id", "category", "order", "weight", "question", "success_criteria"]
            for field in node_required_fields:
                if field not in node:
                    logger.error(f"Node {i} missing required field: {field}")
                    return False
        
        # Validate start_id exists in nodes
        node_ids = [node["id"] for node in scenario["nodes"]]
        if scenario["start_id"] not in node_ids:
            logger.error(f"start_id '{scenario['start_id']}' not found in nodes")
            return False
        
        return True
    
    def save_scenario(self, scenario: Dict[str, Any], output_file: str) -> None:
        """Save generated scenario to file"""
        output_path = self.examples_dir / output_file
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(scenario, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Scenario saved to: {output_path}")
    
    def generate_scenario(self, jd_file: str, role_type: str, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate interview scenario from JD file"""
        logger.info(f"Generating scenario for role type: {role_type}")
        logger.info(f"Reading JD from: {jd_file}")
        
        # Load prompt template
        system_prompt = self.load_prompt_template(role_type)
        
        # Load JD content
        jd_content = self.load_jd_content(jd_file)
        
        # Create user prompt
        user_prompt = f"""
Job Description:

{jd_content}

---

Пожалуйста, создай структурированный сценарий интервью на основе этого JD.
Верни валидный JSON согласно схеме, описанной в системном промпте.
"""
        
        logger.info("Calling LLM Gateway...")
        
        # Call LLM Gateway
        response = self.call_llm_gateway(system_prompt, user_prompt)
        
        logger.info("Parsing LLM response...")
        
        # Parse response
        scenario = self.parse_llm_response(response)
        
        logger.info("Validating scenario...")
        
        # Validate scenario
        if not self.validate_scenario(scenario):
            raise ValueError("Generated scenario validation failed")
        
        # Save scenario
        if output_file:
            self.save_scenario(scenario, output_file)
        
        logger.info("Scenario generation completed successfully!")
        return scenario

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate interview scenarios from Job Descriptions")
    parser.add_argument("jd_file", help="Path to Job Description text file")
    parser.add_argument("role_type", choices=["ba", "it"], help="Role type (ba or it)")
    parser.add_argument("-o", "--output", help="Output file name (default: auto-generated)")
    parser.add_argument("--llm-gw-url", default=LLM_GW_URL, help="LLM Gateway URL")
    parser.add_argument("--dry-run", action="store_true", help="Don't save output, just validate")
    
    args = parser.parse_args()
    
    # Generate output filename if not provided
    if not args.output:
        jd_name = Path(args.jd_file).stem
        args.output = f"{jd_name}_{args.role_type}_generated.json"
    
    try:
        # Initialize generator
        generator = JDScenarioGenerator(args.llm_gw_url)
        
        # Generate scenario
        scenario = generator.generate_scenario(
            jd_file=args.jd_file,
            role_type=args.role_type,
            output_file=None if args.dry_run else args.output
        )
        
        # Print summary
        print("\n" + "="*50)
        print("SCENARIO GENERATION SUMMARY")
        print("="*50)
        print(f"Role Type: {args.role_type}")
        print(f"Scenario ID: {scenario['id']}")
        print(f"Role Profile: {scenario['role_profile']}")
        print(f"Number of Nodes: {len(scenario['nodes'])}")
        print(f"Start Node: {scenario['start_id']}")
        
        # Print categories
        categories = list(set(node['category'] for node in scenario['nodes']))
        print(f"Categories: {', '.join(categories)}")
        
        # Print node summary
        print("\nNode Summary:")
        for node in scenario['nodes']:
            print(f"  {node['id']}: {node['category']} (weight: {node['weight']})")
        
        if not args.dry_run:
            print(f"\nScenario saved to: {args.output}")
        else:
            print("\nDry run completed - scenario validated but not saved")
        
    except Exception as e:
        logger.error(f"Scenario generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
