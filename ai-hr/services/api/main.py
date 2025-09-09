# Основной API сервис AI-HR
import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel, Field

sys.path.append(os.path.join(os.path.dirname(__file__), 'scoring'))
from scoring import QAnswer, score_block, score_overall, analyze_performance

app = FastAPI(title="AI-HR API", version="1.0.0")

SCEN_DIR = Path("/app/data/scenarios")
SCEN_DIR.mkdir(parents=True, exist_ok=True)
REPORT_SERVICE_URL = os.getenv("REPORT_SERVICE_URL", "http://report:8005")
class ScenarioLoad(BaseModel):
    id: str
    schema_version: str = "0.1"
    policy: Dict[str, float] = Field(default_factory=dict)
    nodes: List[Dict]
    start_id: str

class QAnswerIn(BaseModel):
    question_id: str
    block: str
    score: float = Field(..., ge=0.0, le=1.0)
    weight: float = Field(..., ge=0.0, le=1.0)

class BlockScoreIn(BaseModel):
    answers: List[QAnswerIn]
    block_weights: Dict[str, float]

class ReportIn(BaseModel):
    candidate: Dict[str, str]
    vacancy: Dict[str, str]
    blocks: List[Dict[str, float]]

class InterviewAnswer(BaseModel):
    question_text: str
    block: str
    order: int
    weight: float
    score: float
    red_flags: List[str] = Field(default_factory=list)
    timestamps: Dict[str, str] = Field(default_factory=dict)

class InterviewAnswersResponse(BaseModel):
    session_id: str
    total_answers: int
    page: int
    page_size: int
    answers: List[InterviewAnswer]
    positives: List[str] = Field(default_factory=list)
    negatives: List[str] = Field(default_factory=list)
    quotes: List[Dict[str, str]] = Field(default_factory=list)
    rating_0_10: float = Field(..., ge=0.0, le=10.0)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ai-hr-api",
        "timestamp": datetime.now().isoformat(),
        "scenarios_dir": str(SCEN_DIR)
    }

@app.post("/scenario/load")
def scenario_load(payload: ScenarioLoad):
    try:
        scenario_file = SCEN_DIR / f"{payload.id}.json"
        scenario_data = payload.dict()
        scenario_file.write_text(
            json.dumps(scenario_data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        
        return {
            "ok": True,
            "id": payload.id,
            "file": str(scenario_file),
            "nodes_count": len(payload.nodes),
            "message": f"Сценарий '{payload.id}' сохранен"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")

@app.get("/scenario/list")
def scenario_list():
    try:
        scenarios = []
        for scenario_file in SCEN_DIR.glob("*.json"):
            try:
                with open(scenario_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                scenarios.append({
                    "id": scenario_file.stem,
                    "schema_version": data.get("schema_version", "unknown"),
                    "nodes_count": len(data.get("nodes", [])),
                    "start_id": data.get("start_id", "unknown"),
                    "modified": datetime.fromtimestamp(scenario_file.stat().st_mtime).isoformat()
                })
            except Exception as e:
                scenarios.append({
                    "id": scenario_file.stem,
                    "error": str(e)
                })
        
        return {
            "scenarios": scenarios,
            "total": len(scenarios)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list scenarios: {str(e)}")

@app.get("/scenario/{scenario_id}")
def scenario_get(scenario_id: str):
    """Get specific scenario by ID"""
    try:
        scenario_file = SCEN_DIR / f"{scenario_id}.json"
        
        if not scenario_file.exists():
            raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
        
        with open(scenario_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            "id": scenario_id,
            "data": data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load scenario: {str(e)}")

# Scoring
@app.post("/score/aggregate")
def score_aggregate(inp: BlockScoreIn):
    """
    Aggregate scores using BARS system
    
    Args:
        inp: Question answers and block weights
        
    Returns:
        Block scores and overall score
    """
    try:
        # Convert to QAnswer objects
        answers = [
            QAnswer(
                question_id=answer.question_id,
                block=answer.block,
                score=answer.score,
                weight=answer.weight
            )
            for answer in inp.answers
        ]
        
        # Calculate block scores
        blocks = set(answer.block for answer in answers)
        block_scores = {}
        
        for block in blocks:
            score = score_block(answers, block)
            block_scores[block] = score
        
        # Calculate overall score
        overall = score_overall(block_scores, inp.block_weights)
        
        # Get performance analysis
        analysis = analyze_performance(answers, inp.block_weights)
        
        return {
            "block_scores": block_scores,
            "overall": overall,
            "overall_percentage": round(overall * 100, 1),
            "analysis": {
                "strengths": analysis["strengths"],
                "weaknesses": analysis["weaknesses"],
                "overall_level": analysis["overall_level"]
            },
            "summary": {
                "total_questions": len(answers),
                "blocks_assessed": len(blocks),
                "average_score": round(sum(block_scores.values()) / len(block_scores), 3) if block_scores else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Score aggregation failed: {str(e)}")

# Report Generation
@app.post("/report/render")
def report_render(inp: ReportIn):
    """
    Generate PDF report by proxying to report service
    
    Args:
        inp: Report data with candidate, vacancy, and analysis
        
    Returns:
        PDF content or error message
    """
    try:
        # Prepare data for report service
        report_data = {
            "candidate": inp.candidate,
            "vacancy": inp.vacancy,
            "blocks": [
                {
                    "name": block.get("name", "Unknown"),
                    "score": block.get("score", 0.0),
                    "weight": block.get("weight", 0.0)
                }
                for block in inp.blocks
            ],
            "positives": inp.positives,
            "negatives": inp.negatives,
            "quotes": inp.quotes,
            "rating_0_10": inp.rating_0_10
        }
        
        # Call report service
        response = requests.post(
            f"{REPORT_SERVICE_URL}/report",
            json=report_data,
            timeout=30
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "content_type": "application/pdf",
                "size_bytes": len(response.content),
                "preview": response.content[:64].hex() + "...",
                "message": "PDF report generated successfully"
            }
        else:
            return {
                "success": False,
                "error": f"Report service error: {response.status_code}",
                "details": response.text
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Report service unavailable",
            "details": f"Cannot connect to {REPORT_SERVICE_URL}",
            "fallback": "Use /report/html endpoint for HTML version"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@app.post("/report/html")
def report_render_html(inp: ReportIn):
    """
    Generate HTML report (fallback when PDF service is unavailable)
    
    Args:
        inp: Report data with candidate, vacancy, and analysis
        
    Returns:
        HTML content
    """
    try:
        # Prepare data for report service
        report_data = {
            "candidate": inp.candidate,
            "vacancy": inp.vacancy,
            "blocks": [
                {
                    "name": block.get("name", "Unknown"),
                    "score": block.get("score", 0.0),
                    "weight": block.get("weight", 0.0)
                }
                for block in inp.blocks
            ],
            "positives": inp.positives,
            "negatives": inp.negatives,
            "quotes": inp.quotes,
            "rating_0_10": inp.rating_0_10
        }
        
        # Call report service HTML endpoint
        response = requests.post(
            f"{REPORT_SERVICE_URL}/report/html",
            json=report_data,
            timeout=30
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "content_type": "text/html",
                "size_bytes": len(response.content),
                "html": response.text
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Report service error: {response.text}"
            )
            
    except requests.exceptions.ConnectionError:
        # Return simple HTML fallback
        return {
            "success": False,
            "error": "Report service unavailable",
            "fallback_html": f"""
            <html>
            <head><title>Interview Report - {inp.candidate.get('name', 'Candidate')}</title></head>
            <body>
                <h1>Interview Report</h1>
                <h2>Candidate: {inp.candidate.get('name', 'N/A')}</h2>
                <h2>Position: {inp.vacancy.get('title', 'N/A')}</h2>
                <h3>Rating: {inp.rating_0_10}/10</h3>
                <p><strong>Note:</strong> Report service is unavailable. This is a fallback view.</p>
                <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </body>
            </html>
            """
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HTML report generation failed: {str(e)}")

# Interview answers endpoint
@app.get("/interview/{session_id}/answers", response_model=InterviewAnswersResponse)
def get_interview_answers(session_id: str, page: int = 1, page_size: int = 5):
    """Get paginated interview answers for a session"""
    try:
        # Mock data for demonstration - in real implementation, this would come from database
        mock_answers = [
            InterviewAnswer(
                question_text="Опишите опыт настройки антифрод-правил и снижение ложноположительных срабатываний.",
                block="AntiFraud_Rules",
                order=1,
                weight=0.4,
                score=0.8,
                red_flags=[],
                timestamps={"asked": "2024-01-01T10:00:00Z", "answered": "2024-01-01T10:02:30Z"}
            ),
            InterviewAnswer(
                question_text="Расскажите о конкретных кейсах мошенничества, с которыми вы работали.",
                block="AntiFraud_Rules",
                order=2,
                weight=0.6,
                score=0.7,
                red_flags=["generic_response"],
                timestamps={"asked": "2024-01-01T10:03:00Z", "answered": "2024-01-01T10:05:15Z"}
            ),
            InterviewAnswer(
                question_text="Опишите процесс сбора и анализа требований для антифрод-систем.",
                block="Requirements_Engineering",
                order=3,
                weight=0.5,
                score=0.9,
                red_flags=[],
                timestamps={"asked": "2024-01-01T10:06:00Z", "answered": "2024-01-01T10:08:45Z"}
            ),
            InterviewAnswer(
                question_text="Как вы работали с бизнес-пользователями при сборе требований?",
                block="Requirements_Engineering",
                order=4,
                weight=0.3,
                score=0.6,
                red_flags=["unclear_explanation"],
                timestamps={"asked": "2024-01-01T10:09:00Z", "answered": "2024-01-01T10:10:20Z"}
            ),
            InterviewAnswer(
                question_text="Опишите ваш опыт проведения UAT тестирования.",
                block="Testing_UAT",
                order=5,
                weight=0.4,
                score=0.5,
                red_flags=["lack_of_experience", "very_short_response"],
                timestamps={"asked": "2024-01-01T10:11:00Z", "answered": "2024-01-01T10:11:30Z"}
            ),
            InterviewAnswer(
                question_text="Какие инструменты вы использовали для тестирования?",
                block="Testing_UAT",
                order=6,
                weight=0.3,
                score=0.8,
                red_flags=[],
                timestamps={"asked": "2024-01-01T10:12:00Z", "answered": "2024-01-01T10:13:45Z"}
            )
        ]
        
        # Calculate pagination
        total_answers = len(mock_answers)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_answers = mock_answers[start_idx:end_idx]
        
        # Calculate overall rating (0-10 scale)
        if mock_answers:
            weighted_score = sum(answer.score * answer.weight for answer in mock_answers)
            total_weight = sum(answer.weight for answer in mock_answers)
            overall_score = weighted_score / total_weight if total_weight > 0 else 0
            rating_0_10 = overall_score * 10
        else:
            rating_0_10 = 0.0
        
        # Generate positives and negatives
        positives = []
        negatives = []
        quotes = []
        
        for answer in mock_answers:
            if answer.score >= 0.8:
                positives.append(f"Отличный ответ на вопрос {answer.order}: {answer.question_text[:50]}...")
                quotes.append({
                    "question": answer.question_text,
                    "quote": f"Высокая оценка ({answer.score:.2f}) в блоке {answer.block}"
                })
            elif answer.score <= 0.5:
                negatives.append(f"Слабый ответ на вопрос {answer.order}: {answer.question_text[:50]}...")
                quotes.append({
                    "question": answer.question_text,
                    "quote": f"Низкая оценка ({answer.score:.2f}) в блоке {answer.block}"
                })
        
        return InterviewAnswersResponse(
            session_id=session_id,
            total_answers=total_answers,
            page=page,
            page_size=page_size,
            answers=page_answers,
            positives=positives,
            negatives=negatives,
            quotes=quotes,
            rating_0_10=rating_0_10
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get interview answers: {str(e)}")

# Statistics and monitoring
@app.get("/stats")
def get_stats():
    """Get API usage statistics"""
    try:
        scenario_count = len(list(SCEN_DIR.glob("*.json")))
        
        return {
            "scenarios_loaded": scenario_count,
            "data_directory": str(SCEN_DIR),
            "report_service_url": REPORT_SERVICE_URL,
            "api_version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
