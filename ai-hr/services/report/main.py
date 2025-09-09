# Сервис генерации отчетов AI-HR
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from jinja2 import Environment, FileSystemLoader
import weasyprint
from weasyprint import HTML, CSS

app = FastAPI(title="AI-HR Report")

template_dir = os.path.dirname(os.path.abspath(__file__))
jinja_env = Environment(loader=FileSystemLoader(template_dir))

class BlockScore(BaseModel):
    name: str
    score: float = Field(..., ge=0.0, le=1.0)
    weight: float = Field(..., ge=0.0, le=1.0)

class InterviewReport(BaseModel):
    candidate: Dict[str, Any] = Field(..., description="Candidate information")
    vacancy: Dict[str, Any] = Field(..., description="Job vacancy details")
    blocks: List[BlockScore] = Field(..., description="Block scores and weights")
    positives: List[str] = Field(default_factory=list, description="Strengths (>0.7)")
    negatives: List[str] = Field(default_factory=list, description="Weaknesses (<0.7)")
    quotes: List[Dict[str, str]] = Field(default_factory=list, description="Evidence quotes")
    rating_0_10: float = Field(..., ge=0.0, le=10.0, description="Overall rating 0-10")

def calculate_overall_match(blocks: List[BlockScore]) -> float:
    """Calculate overall match percentage from block scores"""
    if not blocks:
        return 0.0
    
    weighted_sum = sum(block.score * block.weight for block in blocks)
    total_weight = sum(block.weight for block in blocks)
    
    if total_weight == 0:
        return 0.0
    
    return round((weighted_sum / total_weight) * 100, 1)

def get_rating_description(rating: float) -> str:
    """Get human-readable rating description"""
    if rating >= 9.0:
        return "Excellent"
    elif rating >= 7.0:
        return "Good"
    elif rating >= 5.0:
        return "Average"
    elif rating >= 3.0:
        return "Below Average"
    else:
        return "Poor"

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "report", "timestamp": datetime.now().isoformat()}

@app.post("/report")
def generate_report(report_data: InterviewReport):
    """
    Generate PDF report from interview data
    
    Args:
        report_data: Interview results with candidate info, scores, and analysis
        
    Returns:
        PDF file as application/pdf response
    """
    try:
        # Calculate overall match percentage
        overall_match = calculate_overall_match(report_data.blocks)
        
        # Prepare template data
        template_data = {
            "candidate": report_data.candidate,
            "vacancy": report_data.vacancy,
            "blocks": report_data.blocks,
            "positives": report_data.positives,
            "negatives": report_data.negatives,
            "quotes": report_data.quotes,
            "rating": report_data.rating_0_10,
            "rating_description": get_rating_description(report_data.rating_0_10),
            "overall_match": overall_match,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "report_id": f"HR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        }
        
        # Render HTML template
        template = jinja_env.get_template("template.html")
        html_content = template.render(**template_data)
        
        # Generate PDF using WeasyPrint
        html_doc = HTML(string=html_content)
        
        # Add CSS for better styling
        css = CSS(string="""
            @page {
                size: A4;
                margin: 2cm;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
            }
            .header {
                text-align: center;
                border-bottom: 3px solid #2c3e50;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }
            .match-score {
                font-size: 2.5em;
                font-weight: bold;
                color: #27ae60;
                margin: 10px 0;
            }
            .rating {
                font-size: 1.8em;
                font-weight: bold;
                color: #3498db;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }
            th {
                background-color: #f8f9fa;
                font-weight: bold;
            }
            .strengths, .weaknesses {
                margin: 20px 0;
            }
            .strengths h3 {
                color: #27ae60;
            }
            .weaknesses h3 {
                color: #e74c3c;
            }
            .quotes {
                margin: 20px 0;
            }
            .quote {
                background-color: #f8f9fa;
                border-left: 4px solid #3498db;
                padding: 15px;
                margin: 10px 0;
                font-style: italic;
            }
            .quote-source {
                font-weight: bold;
                margin-top: 5px;
            }
        """)
        
        # Generate PDF
        pdf_bytes = html_doc.write_pdf(stylesheets=[css])
        
        # Return PDF response
        filename = f"interview_report_{template_data['report_id']}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@app.post("/report/html")
def generate_html_report(report_data: InterviewReport):
    """
    Generate HTML report (fallback if PDF generation fails)
    
    Returns:
        HTML content for debugging or manual PDF conversion
    """
    try:
        # Calculate overall match percentage
        overall_match = calculate_overall_match(report_data.blocks)
        
        # Prepare template data
        template_data = {
            "candidate": report_data.candidate,
            "vacancy": report_data.vacancy,
            "blocks": report_data.blocks,
            "positives": report_data.positives,
            "negatives": report_data.negatives,
            "quotes": report_data.quotes,
            "rating": report_data.rating_0_10,
            "rating_description": get_rating_description(report_data.rating_0_10),
            "overall_match": overall_match,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "report_id": f"HR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        }
        
        # Render HTML template
        template = jinja_env.get_template("template.html")
        html_content = template.render(**template_data)
        
        return Response(
            content=html_content,
            media_type="text/html"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HTML report generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
