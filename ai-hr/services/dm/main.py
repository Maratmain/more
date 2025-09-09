# Менеджер диалогов AI-HR
import os
import sys
import yaml
import random
import json
import requests
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from models import ReplyIn, ReplyOut

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'api'))
from scenario import load_scenario, next_node, get_profile_threshold

load_dotenv()
DRILL_THRESHOLD = float(os.getenv("DRILL_THRESHOLD", "0.7"))

LLM_ENGINE = os.getenv("LLM_ENGINE", "llama.cpp")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "llama.cpp")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://llm-local:8080/v1")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://llm-vllm:8000/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5-7b-instruct")
LLM_JSON_SCHEMA_ENFORCE = os.getenv("LLM_JSON_SCHEMA_ENFORCE", "true").lower() == "true"

app = FastAPI(title="AI-HR DM")

# Load backchannel configuration
BACKCHANNEL_CONFIG_PATH = Path(__file__).parent / "config" / "backchannel.yaml"

def load_backchannel_config():
    """Load backchannel configuration from YAML file"""
    try:
        with open(BACKCHANNEL_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: Could not load backchannel config: {e}")
        return None

BACKCHANNEL_CONFIG = load_backchannel_config()

# Load JSON schemas
JSON_SCHEMA_DIR = Path(__file__).parent / "json_schema"

def load_json_schema(schema_name: str) -> Dict[str, Any]:
    """Load JSON schema from file"""
    try:
        schema_path = JSON_SCHEMA_DIR / f"{schema_name}.json"
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load JSON schema {schema_name}: {e}")
        return None

# Load schemas
REPLY_OUT_SCHEMA = load_json_schema("ReplyOut")
JUDGE_RESPONSE_SCHEMA = load_json_schema("JudgeResponse")
PLANNER_RESPONSE_SCHEMA = load_json_schema("PlannerResponse")

# LLM Integration Functions
def call_local_llm(system_prompt: str, user_prompt: str, stream: bool = True, json_schema: Dict[str, Any] = None) -> Dict[str, Any]:
    """Call local LLM with JSON schema enforcement"""
    try:
        # Determine which LLM service to use
        if LLM_ENGINE == "llama.cpp":
            base_url = LLM_BASE_URL
            model = LLM_MODEL
        elif LLM_PROVIDER == "openai_compatible":
            base_url = OPENAI_BASE_URL
            model = LLM_MODEL
        else:
            # Fallback to heuristic scoring
            return {"error": "No LLM service configured"}
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": stream,
            "temperature": 0.1,
            "max_tokens": 96  # Limit for SLA ≤5s compliance
        }
        
        # Add JSON schema enforcement
        if LLM_JSON_SCHEMA_ENFORCE:
            if json_schema:
                if LLM_ENGINE == "llama.cpp":
                    # llama.cpp uses grammar-json-schema with specific schema
                    payload["response_format"] = {"type": "json_object", "schema": json_schema}
                elif LLM_PROVIDER == "openai_compatible":
                    # OpenAI-compatible uses response_format with schema
                    payload["response_format"] = {"type": "json_object", "schema": json_schema}
            else:
                # Default JSON object format
                if LLM_ENGINE == "llama.cpp":
                    payload["response_format"] = {"type": "json_object"}
                elif LLM_PROVIDER == "openai_compatible":
                    payload["response_format"] = {"type": "json_object"}
        
        # Make request
        response = requests.post(
            f"{base_url}/chat/completions",
            json=payload,
            stream=stream,
            timeout=30
        )
        
        if response.status_code == 200:
            if stream:
                # Handle streaming response
                full_content = ""
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]  # Remove 'data: ' prefix
                            if data_str.strip() == '[DONE]':
                                break
                            try:
                                data = json.loads(data_str)
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        full_content += delta['content']
                            except json.JSONDecodeError:
                                continue
                
                # Parse the complete JSON response
                try:
                    return json.loads(full_content)
                except json.JSONDecodeError:
                    return {"error": "Invalid JSON response from LLM"}
            else:
                # Handle non-streaming response
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0]['message']['content']
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        return {"error": "Invalid JSON response from LLM"}
                else:
                    return {"error": "No response from LLM"}
        else:
            return {"error": f"LLM request failed: {response.status_code}"}
            
    except requests.exceptions.RequestException as e:
        return {"error": f"LLM connection error: {str(e)}"}
    except Exception as e:
        return {"error": f"LLM processing error: {str(e)}"}

def get_backchannel_response(role_profile: Optional[str] = None, score: float = 0.5) -> str:
    """Get backchannel response for immediate feedback"""
    if not BACKCHANNEL_CONFIG:
        return "Понимаю."
    
    roles = BACKCHANNEL_CONFIG.get("roles", {})
    common = BACKCHANNEL_CONFIG.get("common", {})
    selection = BACKCHANNEL_CONFIG.get("selection", {})
    
    # Get role-specific responses
    role_config = roles.get(role_profile, {}) if role_profile else {}
    
    # Determine response type based on score
    positive_threshold = selection.get("positive_threshold", 0.7)
    negative_threshold = selection.get("negative_threshold", 0.3)
    
    if score >= positive_threshold:
        responses = role_config.get("positive", common.get("generic_positive", ["Понимаю."]))
    elif score <= negative_threshold:
        responses = role_config.get("negative", common.get("generic_negative", ["Понял, но нужны детали."]))
    else:
        responses = role_config.get("neutral", common.get("generic_neutral", ["Уточните, пожалуйста."]))
    
    return random.choice(responses) if responses else "Понимаю."

def stream_llm_response(system_prompt: str, user_prompt: str, json_schema: Dict[str, Any] = None):
    """Stream LLM response for real-time feedback"""
    try:
        # Determine which LLM service to use
        if LLM_ENGINE == "llama.cpp":
            base_url = LLM_BASE_URL
            model = LLM_MODEL
        elif LLM_PROVIDER == "openai_compatible":
            base_url = OPENAI_BASE_URL
            model = LLM_MODEL
        else:
            yield f"data: {json.dumps({'error': 'No LLM service configured'})}\n\n"
            return
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": True,
            "temperature": 0.1,
            "max_tokens": 96
        }
        
        # Add JSON schema enforcement
        if json_schema:
            if LLM_ENGINE == "llama.cpp":
                payload["response_format"] = {"type": "json_object", "schema": json_schema}
            elif LLM_PROVIDER == "openai_compatible":
                payload["response_format"] = {"type": "json_object", "schema": json_schema}
        else:
            if LLM_ENGINE == "llama.cpp":
                payload["response_format"] = {"type": "json_object"}
            elif LLM_PROVIDER == "openai_compatible":
                payload["response_format"] = {"type": "json_object"}
        
        # Make streaming request
        response = requests.post(
            f"{base_url}/chat/completions",
            json=payload,
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        if data_str.strip() == '[DONE]':
                            yield f"data: {json.dumps({'done': True})}\n\n"
                            break
                        try:
                            data = json.loads(data_str)
                            yield f"data: {json.dumps(data)}\n\n"
                        except json.JSONDecodeError:
                            continue
        else:
            yield f"data: {json.dumps({'error': f'LLM request failed: {response.status_code}'})}\n\n"
            
    except Exception as e:
        yield f"data: {json.dumps({'error': f'LLM streaming error: {str(e)}'})}\n\n"

def judge_response(transcript: str, success_criteria: list[str], role_profile: Optional[str] = None) -> Dict[str, Any]:
    """Judge candidate response against success criteria"""
    
    # Create system prompt with success criteria
    system_prompt = f"""Ты эксперт-оценщик для роли {role_profile or 'общей'}. 
    Оцени ответ кандидата строго по заданным критериям успеха.
    НЕ выдумывай критерии - используй только те, что предоставлены.
    
    Критерии успеха: {', '.join(success_criteria)}
    
    Верни JSON строго по схеме: {{"score": 0.0-1.0, "evidence": ["доказательство1", "доказательство2"], "confidence": 0.0-1.0, "missing_criteria": ["критерий1", "критерий2"]}}"""
    
    user_prompt = f"""Ответ кандидата: "{transcript}"
    
    Оцени по критериям и верни JSON."""
    
    # Call LLM with judge schema
    judge_response = call_local_llm(system_prompt, user_prompt, stream=False, json_schema=JUDGE_RESPONSE_SCHEMA)
    
    if "error" in judge_response:
        # Fallback to heuristic scoring
        score = heuristic_score(transcript, success_criteria)
        return {
            "score": score,
            "evidence": [f"Найдено {len([c for c in success_criteria if c.lower() in transcript.lower()])} из {len(success_criteria)} критериев"],
            "confidence": 0.5,
            "missing_criteria": [c for c in success_criteria if c.lower() not in transcript.lower()],
            "error": judge_response["error"]
        }
    
    return judge_response

def plan_followup(judge_result: Dict[str, Any], node: Any, role_profile: Optional[str] = None) -> Dict[str, Any]:
    """Plan follow-up based on judge evaluation"""
    
    score = judge_result.get("score", 0.0)
    missing_criteria = judge_result.get("missing_criteria", [])
    
    # Create system prompt
    system_prompt = f"""Ты интервьюер для роли {role_profile or 'общей'}.
    На основе оценки ответа кандидата сформулируй короткий follow-up вопрос.
    
    Если score < 0.7, задай 1 короткий уточняющий вопрос.
    Если score >= 0.7, переходи к следующему узлу.
    
    Верни JSON строго по схеме: {{"reply": "короткий вопрос", "next_node_id": "следующий_узел", "follow_up_type": "тип", "priority": "high/medium/low"}}"""
    
    user_prompt = f"""Оценка: {score}
    Отсутствующие критерии: {', '.join(missing_criteria) if missing_criteria else 'Нет'}
    Текущий узел: {node.category}
    Следующий узел при успехе: {node.next_if_pass}
    Следующий узел при неудаче: {node.next_if_fail}
    
    Сформулируй follow-up."""
    
    # Call LLM with planner schema
    planner_response = call_local_llm(system_prompt, user_prompt, stream=False, json_schema=PLANNER_RESPONSE_SCHEMA)
    
    if "error" in planner_response:
        # Fallback logic
        if score < 0.7:
            reply = f"Уточните, пожалуйста, детали по {missing_criteria[0] if missing_criteria else 'этому вопросу'}."
            next_node_id = node.next_if_fail
        else:
            reply = "Понял, переходим дальше."
            next_node_id = node.next_if_pass
        
        return {
            "reply": reply,
            "next_node_id": next_node_id,
            "follow_up_type": "clarification" if score < 0.7 else "completion",
            "priority": "high" if score < 0.7 else "medium",
            "error": planner_response["error"]
        }
    
    return planner_response

def generate_llm_response(node: Any, transcript: str, scores: Dict[str, float], 
                         role_profile: Optional[str] = None) -> Dict[str, Any]:
    """Generate LLM response using judge-planner pattern"""
    
    try:
        # Step 1: Judge the response
        judge_result = judge_response(transcript, node.success_criteria, role_profile)
        
        if "error" in judge_result:
            # Fallback to heuristic scoring
            score = heuristic_score(transcript, node.success_criteria)
            return {
                "reply": get_role_specific_response(role_profile, score, 0.5),
                "next_node_id": node.next_if_fail if score < 0.7 else node.next_if_pass,
                "scoring_update": {"block": node.category, "delta": score - scores.get(node.category, 0.0), "score": score},
                "red_flags": ["judge_error"],
                "judge_error": judge_result["error"]
            }
        
        # Step 2: Plan follow-up based on judge result
        planner_result = plan_followup(judge_result, node, role_profile)
        
        if "error" in planner_result:
            # Use judge result with fallback planning
            score = judge_result.get("score", 0.5)
            if score < 0.7:
                reply = f"Уточните, пожалуйста, детали по {judge_result.get('missing_criteria', ['этому вопросу'])[0]}."
                next_node_id = node.next_if_fail
            else:
                reply = "Понял, переходим дальше."
                next_node_id = node.next_if_pass
            
            return {
                "reply": reply,
                "next_node_id": next_node_id,
                "scoring_update": {"block": node.category, "delta": score - scores.get(node.category, 0.0), "score": score},
                "red_flags": ["planner_error"],
                "planner_error": planner_result["error"]
            }
        
        # Step 3: Combine judge and planner results
        score = judge_result.get("score", 0.5)
        confidence = judge_result.get("confidence", 0.5)
        
        # Determine red flags
        red_flags = []
        if confidence < 0.4:
            red_flags.append("low_confidence")
        if len(transcript.strip()) < 10:
            red_flags.append("very_short_response")
        if judge_result.get("missing_criteria"):
            red_flags.append("missing_keywords")
        
        return {
            "reply": planner_result.get("reply", "Понимаю."),
            "next_node_id": planner_result.get("next_node_id"),
            "scoring_update": {
                "block": node.category,
                "delta": score - scores.get(node.category, 0.0),
                "score": score
            },
            "red_flags": red_flags,
            "judge_evidence": judge_result.get("evidence", []),
            "planner_type": planner_result.get("follow_up_type", "clarification")
        }
        
    except Exception as e:
        # Complete fallback to heuristic scoring
        score = heuristic_score(transcript, node.success_criteria)
        return {
            "reply": get_role_specific_response(role_profile, score, 0.5),
            "next_node_id": node.next_if_fail if score < 0.7 else node.next_if_pass,
            "scoring_update": {"block": node.category, "delta": score - scores.get(node.category, 0.0), "score": score},
            "red_flags": ["system_error"],
            "system_error": str(e)
        }

def heuristic_score(transcript: str, criteria: list[str]) -> float:
    """Calculate heuristic score based on keyword matches"""
    t = transcript.lower()
    hits = sum(1 for c in criteria if c.lower() in t)
    if hits == 0: return 0.3
    if hits < len(criteria): return 0.7
    return 1.0

def calculate_confidence(transcript: str, criteria: list[str], score: float) -> float:
    """Calculate confidence based on score and transcript quality"""
    # Base confidence from score
    base_confidence = score
    
    # Adjust based on transcript length and quality
    transcript_length = len(transcript.strip())
    if transcript_length < 10:
        base_confidence *= 0.5  # Very short responses are less confident
    elif transcript_length > 200:
        base_confidence *= 1.1  # Longer responses can be more confident
    
    # Adjust based on keyword density
    t = transcript.lower()
    keyword_density = sum(1 for c in criteria if c.lower() in t) / len(criteria)
    base_confidence *= (0.5 + keyword_density * 0.5)
    
    return min(1.0, max(0.0, base_confidence))

def get_role_specific_response(role_profile: str, score: float, confidence: float) -> str:
    """Get role-specific backchannel response based on score and confidence"""
    if not BACKCHANNEL_CONFIG or not role_profile:
        # Fallback to generic responses
        if score >= 0.7:
            return "Понимаю."
        elif score >= 0.4:
            return "Уточните, пожалуйста."
        else:
            return "Понял, но нужны детали."
    
    # Get role-specific responses
    role_config = BACKCHANNEL_CONFIG.get("roles", {}).get(role_profile)
    if not role_config:
        # Fallback to generic
        return get_generic_response(score)
    
    # Select response type based on score
    if score >= BACKCHANNEL_CONFIG.get("selection", {}).get("positive_threshold", 0.7):
        responses = role_config.get("positive", [])
    elif score <= BACKCHANNEL_CONFIG.get("selection", {}).get("negative_threshold", 0.3):
        responses = role_config.get("negative", [])
    else:
        responses = role_config.get("neutral", [])
    
    # Select random response from the appropriate category
    if responses:
        return random.choice(responses)
    else:
        return get_generic_response(score)

def get_generic_response(score: float) -> str:
    """Get generic response when role-specific responses are not available"""
    if not BACKCHANNEL_CONFIG:
        if score >= 0.7:
            return "Понимаю."
        elif score >= 0.4:
            return "Уточните, пожалуйста."
        else:
            return "Понял, но нужны детали."
    
    common = BACKCHANNEL_CONFIG.get("common", {})
    if score >= 0.7:
        responses = common.get("generic_positive", ["Понимаю."])
    elif score >= 0.4:
        responses = common.get("generic_neutral", ["Уточните, пожалуйста."])
    else:
        responses = common.get("generic_negative", ["Понял, но нужны детали."])
    
    return random.choice(responses) if responses else "Понимаю."

@app.post("/reply", response_model=ReplyOut)
def reply(inp: ReplyIn):
    # Try LLM-based response first if configured
    if LLM_ENGINE in ["llama.cpp", "openai_compatible"] or LLM_PROVIDER in ["llama.cpp", "openai_compatible"]:
        try:
            print(f"Using LLM engine: {LLM_ENGINE}, provider: {LLM_PROVIDER}")
            llm_response = generate_llm_response(
                inp.node, 
                inp.transcript, 
                inp.scores, 
                inp.role_profile
            )
            
            # If LLM response is successful, use it
            if "error" not in llm_response:
                return ReplyOut(
                    reply=llm_response.get("reply", "Понимаю."),
                    next_node_id=llm_response.get("next_node_id"),
                    scoring_update=llm_response.get("scoring_update", {}),
                    red_flags=llm_response.get("red_flags", []),
                    delta_score=llm_response.get("scoring_update", {}).get("delta", 0.0),
                    confidence=0.8,  # LLM responses have higher confidence
                    role_profile=inp.role_profile
                )
            else:
                print(f"LLM error, falling back to heuristic: {llm_response['error']}")
        except Exception as e:
            print(f"LLM integration error, falling back to heuristic: {e}")
    
    # Fallback to heuristic scoring
    # Load scenario for the category
    try:
        scenario = load_scenario(inp.node.category)
    except Exception as e:
        print(f"Failed to load scenario: {e}")
        # Fallback to simple logic
        scenario = None
    
    # Calculate score and confidence
    score = heuristic_score(inp.transcript, inp.node.success_criteria)
    confidence = calculate_confidence(inp.transcript, inp.node.success_criteria, score)
    delta = score - inp.scores.get(inp.node.category, 0.0)

    # Determine drill threshold based on role profile
    drill_threshold = DRILL_THRESHOLD  # Default fallback
    if inp.role_profile:
        try:
            drill_threshold = get_profile_threshold(inp.role_profile)
        except Exception as e:
            print(f"Could not get profile threshold: {e}")

    # Use scenario selector if available, otherwise fallback
    if scenario:
        next_id = next_node(inp.node, score, scenario)
    else:
        # Fallback logic with role-specific threshold
        next_id = inp.node.next_if_fail if score < drill_threshold else inp.node.next_if_pass

    # Generate role-specific response
    reply_text = get_role_specific_response(inp.role_profile, score, confidence)
    
    # Detect red flags
    red_flags = []
    if "не уверен" in inp.transcript.lower():
        red_flags.append("low_confidence")
    if confidence < 0.4:
        red_flags.append("low_confidence")
    if len(inp.transcript.strip()) < 10:
        red_flags.append("very_short_response")

    return ReplyOut(
        reply=reply_text,
        next_node_id=next_id,
        scoring_update={"block": inp.node.category, "delta": delta, "score": score},
        red_flags=red_flags,
        delta_score=delta,
        confidence=confidence,
        role_profile=inp.role_profile
    )

@app.post("/reply/stream")
def reply_stream(inp: ReplyIn):
    """Streaming reply endpoint with backchannel support"""
    
    def generate_stream():
        # Start timing
        start_time = time.time()
        
        # Get initial backchannel response
        backchannel_response = get_backchannel_response(inp.role_profile, 0.5)
        
        # Send backchannel immediately
        yield f"data: {json.dumps({'type': 'backchannel', 'response': backchannel_response})}\n\n"
        
        # Try LLM-based response first if configured
        if LLM_ENGINE in ["llama.cpp", "openai_compatible"] or LLM_PROVIDER in ["llama.cpp", "openai_compatible"]:
            try:
                # Step 1: Judge the response
                judge_result = judge_response(inp.transcript, inp.node.success_criteria, inp.role_profile)
                
                if "error" not in judge_result:
                    # Step 2: Plan follow-up based on judge result
                    planner_result = plan_followup(judge_result, inp.node, inp.role_profile)
                    
                    if "error" not in planner_result:
                        # Send judge result
                        yield f"data: {json.dumps({'type': 'judge', 'result': judge_result})}\n\n"
                        
                        # Send planner result
                        yield f"data: {json.dumps({'type': 'planner', 'result': planner_result})}\n\n"
                        
                        # Calculate final response
                        score = judge_result.get("score", 0.5)
                        confidence = judge_result.get("confidence", 0.5)
                        
                        # Determine red flags
                        red_flags = []
                        if confidence < 0.4:
                            red_flags.append("low_confidence")
                        if len(inp.transcript.strip()) < 10:
                            red_flags.append("very_short_response")
                        if judge_result.get("missing_criteria"):
                            red_flags.append("missing_keywords")
                        
                        final_response = {
                            "type": "final",
                            "reply": planner_result.get("reply", "Понимаю."),
                            "next_node_id": planner_result.get("next_node_id"),
                            "scoring_update": {
                                "block": inp.node.category,
                                "delta": score - inp.scores.get(inp.node.category, 0.0),
                                "score": score
                            },
                            "red_flags": red_flags,
                            "delta_score": score - inp.scores.get(inp.node.category, 0.0),
                            "confidence": confidence,
                            "role_profile": inp.role_profile,
                            "judge_evidence": judge_result.get("evidence", []),
                            "planner_type": planner_result.get("follow_up_type", "clarification")
                        }
                        
                        yield f"data: {json.dumps(final_response)}\n\n"
                        
                        # Record metrics
                        end_time = time.time()
                        dm_latency_ms = (end_time - start_time) * 1000
                        
                        try:
                            metrics_request = {
                                "service": "dm",
                                "latency_ms": dm_latency_ms,
                                "session_id": f"stream_{int(time.time())}",
                                "turn_id": f"turn_{int(time.time())}"
                            }
                            requests.post("http://localhost:8010/latency", json=metrics_request, timeout=1)
                        except:
                            pass  # Ignore metrics errors
                        
                        yield f"data: {json.dumps({'type': 'done', 'latency_ms': dm_latency_ms})}\n\n"
                        return
                
                # Fallback to heuristic if LLM fails
                yield f"data: {json.dumps({'type': 'fallback', 'reason': 'LLM error'})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
                return
        
        # Fallback to heuristic scoring
        score = heuristic_score(inp.transcript, inp.node.success_criteria)
        confidence = calculate_confidence(inp.transcript, inp.node.success_criteria, score)
        delta = score - inp.scores.get(inp.node.category, 0.0)
        
        # Determine drill threshold based on role profile
        drill_threshold = DRILL_THRESHOLD
        if inp.role_profile:
            try:
                drill_threshold = get_profile_threshold(inp.role_profile)
            except Exception:
                pass
        
        # Use scenario selector if available, otherwise fallback
        try:
            scenario = load_scenario(inp.node.category)
            next_id = next_node(inp.node, score, scenario) if scenario else None
        except Exception:
            next_id = None
        
        if not next_id:
            next_id = inp.node.next_if_fail if score < drill_threshold else inp.node.next_if_pass
        
        # Generate role-specific response
        reply_text = get_role_specific_response(inp.role_profile, score, confidence)
        
        # Detect red flags
        red_flags = []
        if "не уверен" in inp.transcript.lower():
            red_flags.append("low_confidence")
        if confidence < 0.4:
            red_flags.append("low_confidence")
        if len(inp.transcript.strip()) < 10:
            red_flags.append("very_short_response")
        
        final_response = {
            "type": "final",
            "reply": reply_text,
            "next_node_id": next_id,
            "scoring_update": {"block": inp.node.category, "delta": delta, "score": score},
            "red_flags": red_flags,
            "delta_score": delta,
            "confidence": confidence,
            "role_profile": inp.role_profile
        }
        
        yield f"data: {json.dumps(final_response)}\n\n"
        
        # Record metrics
        end_time = time.time()
        dm_latency_ms = (end_time - start_time) * 1000
        
        try:
            metrics_request = {
                "service": "dm",
                "latency_ms": dm_latency_ms,
                "session_id": f"stream_{int(time.time())}",
                "turn_id": f"turn_{int(time.time())}"
            }
            requests.post("http://localhost:8010/latency", json=metrics_request, timeout=1)
        except:
            pass  # Ignore metrics errors
        
        yield f"data: {json.dumps({'type': 'done', 'latency_ms': dm_latency_ms})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "dialog-manager",
        "backchannel_config_loaded": BACKCHANNEL_CONFIG is not None,
        "drill_threshold": DRILL_THRESHOLD,
        "llm_config": {
            "engine": LLM_ENGINE,
            "provider": LLM_PROVIDER,
            "base_url": LLM_BASE_URL,
            "model": LLM_MODEL,
            "openai_base_url": OPENAI_BASE_URL
        },
        "timestamp": "2024-01-01T00:00:00Z"  # You can add datetime import if needed
    }

@app.get("/config/backchannel")
def get_backchannel_config():
    """Get backchannel configuration"""
    if not BACKCHANNEL_CONFIG:
        return {"error": "Backchannel configuration not loaded"}
    
    return {
        "config": BACKCHANNEL_CONFIG,
        "status": "loaded"
    }

@app.get("/roles")
def get_supported_roles():
    """Get list of supported role profiles"""
    if not BACKCHANNEL_CONFIG:
        return {"roles": [], "error": "Configuration not loaded"}
    
    roles = list(BACKCHANNEL_CONFIG.get("roles", {}).keys())
    return {
        "roles": roles,
        "total": len(roles)
    }
