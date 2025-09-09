# Сервис обработки резюме
import os
import io
import uuid
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

import pdfplumber
from docx import Document
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from .mapping_rules import analyze_cv_mapping, map_cv_to_role_categories

load_dotenv()

app = FastAPI(title="AI-HR CV Service")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "cv_chunks")
EMBEDDER_MODEL = os.getenv("EMBEDDER", "sentence-transformers/all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

# Initialize components
print(f"Loading embedding model: {EMBEDDER_MODEL}")
embedder = SentenceTransformer(EMBEDDER_MODEL)

# Initialize Qdrant client
qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

# Pydantic models
class CVProcessResult(BaseModel):
    cv_id: str
    filename: str
    chunks_created: int
    total_text_length: int
    processing_time: float
    status: str

class CVSearchRequest(BaseModel):
    query: str
    limit: int = 5
    score_threshold: float = 0.7

class CVSearchResult(BaseModel):
    cv_id: str
    chunk_text: str
    score: float
    offset: int

class CVMappingRequest(BaseModel):
    cv_id: str
    role_type: str = "ba"  # "ba" or "it"

class CVMappingResult(BaseModel):
    cv_id: str
    role_type: str
    priority_level: str
    detected_blocks: Dict[str, Dict[str, any]]
    missing_blocks: List[str]
    total_categories: int
    covered_categories: int
    recommendations: Dict[str, any]

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file"""
    try:
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            text_parts = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n".join(text_parts)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF extraction failed: {str(e)}")

def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file"""
    try:
        doc = Document(io.BytesIO(file_content))
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text.strip())
        return "\n".join(text_parts)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"DOCX extraction failed: {str(e)}")

def extract_text_fallback(file_content: bytes, filename: str) -> str:
    """Fallback text extraction (plain text only)"""
    try:
        # Try to decode as UTF-8
        text = file_content.decode('utf-8')
        return text
    except UnicodeDecodeError:
        # Try other encodings
        for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
            try:
                text = file_content.decode(encoding)
                return text
            except UnicodeDecodeError:
                continue
        raise HTTPException(status_code=400, detail="Unable to decode file content")

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            for i in range(end, max(start + chunk_size // 2, end - 100), -1):
                if text[i] in '.!?':
                    end = i + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks

def ensure_collection_exists():
    """Ensure Qdrant collection exists with correct configuration"""
    try:
        # Get collection info
        collections = qdrant_client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if QDRANT_COLLECTION not in collection_names:
            # Create collection
            qdrant_client.create_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=VectorParams(
                    size=embedder.get_sentence_embedding_dimension(),
                    distance=Distance.COSINE
                )
            )
            print(f"Created collection: {QDRANT_COLLECTION}")
        else:
            print(f"Collection exists: {QDRANT_COLLECTION}")
            
    except Exception as e:
        print(f"Warning: Could not ensure collection exists: {e}")

# Initialize collection on startup
ensure_collection_exists()

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Test Qdrant connection
        collections = qdrant_client.get_collections()
        qdrant_status = "connected"
    except Exception as e:
        qdrant_status = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "service": "cv-processing",
        "embedder_model": EMBEDDER_MODEL,
        "qdrant_status": qdrant_status,
        "collection": QDRANT_COLLECTION,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/ingest", response_model=CVProcessResult)
async def ingest_cv(file: UploadFile = File(...)):
    """
    Process CV file and store embeddings in Qdrant
    
    Args:
        file: PDF or DOCX file
        
    Returns:
        Processing result with statistics
    """
    start_time = datetime.now()
    
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ['.pdf', '.docx', '.txt']:
        raise HTTPException(
            status_code=400, 
            detail="Unsupported file type. Supported: .pdf, .docx, .txt"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Generate CV ID
        cv_id = str(uuid.uuid4())
        
        # Extract text based on file type
        if file_extension == '.pdf':
            text = extract_text_from_pdf(file_content)
        elif file_extension == '.docx':
            text = extract_text_from_docx(file_content)
        else:  # .txt
            text = extract_text_fallback(file_content, file.filename)
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text content found in file")
        
        # Split into chunks
        chunks = chunk_text(text)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No text chunks created")
        
        # Generate embeddings
        print(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = embedder.encode(chunks)
        
        # Prepare points for Qdrant
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding.tolist(),
                payload={
                    "cv_id": cv_id,
                    "filename": file.filename,
                    "chunk_index": i,
                    "chunk_text": chunk,
                    "text_length": len(chunk),
                    "uploaded_at": datetime.now().isoformat()
                }
            )
            points.append(point)
        
        # Store in Qdrant
        print(f"Storing {len(points)} points in Qdrant...")
        qdrant_client.upsert(
            collection_name=QDRANT_COLLECTION,
            points=points
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return CVProcessResult(
            cv_id=cv_id,
            filename=file.filename,
            chunks_created=len(chunks),
            total_text_length=len(text),
            processing_time=processing_time,
            status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/search", response_model=List[CVSearchResult])
def search_cvs(request: CVSearchRequest):
    """
    Search CVs using semantic similarity
    
    Args:
        request: Search query and parameters
        
    Returns:
        List of matching CV chunks
    """
    try:
        # Generate query embedding
        query_embedding = embedder.encode([request.query])[0]
        
        # Search in Qdrant
        search_results = qdrant_client.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=query_embedding.tolist(),
            limit=request.limit,
            score_threshold=request.score_threshold
        )
        
        # Format results
        results = []
        for result in search_results:
            results.append(CVSearchResult(
                cv_id=result.payload["cv_id"],
                chunk_text=result.payload["chunk_text"],
                score=result.score,
                offset=result.payload["chunk_index"]
            ))
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/cvs")
def list_cvs():
    """List all CVs in the database"""
    try:
        # Get all points (this is a simple implementation)
        # In production, you might want to use scroll or search with filters
        search_results = qdrant_client.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=1000
        )[0]
        
        # Group by CV ID
        cvs = {}
        for point in search_results:
            cv_id = point.payload["cv_id"]
            if cv_id not in cvs:
                cvs[cv_id] = {
                    "cv_id": cv_id,
                    "filename": point.payload["filename"],
                    "uploaded_at": point.payload["uploaded_at"],
                    "chunks_count": 0
                }
            cvs[cv_id]["chunks_count"] += 1
        
        return {
            "cvs": list(cvs.values()),
            "total": len(cvs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list CVs: {str(e)}")

@app.get("/cvs/list")
def list_cvs_simple():
    """Simple list of CV IDs for admin UI"""
    try:
        search_results = qdrant_client.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=1000
        )[0]
        
        # Get unique CV IDs
        cv_ids = list(set(point.payload["cv_id"] for point in search_results))
        
        return {
            "cv_ids": cv_ids,
            "total": len(cv_ids)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list CV IDs: {str(e)}")

@app.get("/cvs/search")
def search_cvs_simple(q: str, top_k: int = 5):
    """Simple search endpoint for admin UI"""
    try:
        if not q.strip():
            raise HTTPException(status_code=400, detail="Query parameter 'q' is required")
        
        # Generate query embedding
        query_embedding = embedder.encode([q])[0]
        
        # Search in Qdrant
        search_results = qdrant_client.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=query_embedding.tolist(),
            limit=top_k,
            score_threshold=0.3
        )
        
        # Format results
        results = []
        for result in search_results:
            results.append({
                "cv_id": result.payload["cv_id"],
                "filename": result.payload["filename"],
                "chunk_text": result.payload["chunk_text"],
                "score": result.score,
                "chunk_index": result.payload["chunk_index"]
            })
        
        return {
            "query": q,
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.delete("/cvs/{cv_id}")
def delete_cv(cv_id: str):
    """Delete a CV and all its chunks"""
    try:
        # Find all points for this CV
        search_results = qdrant_client.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=1000
        )[0]
        
        points_to_delete = []
        for point in search_results:
            if point.payload["cv_id"] == cv_id:
                points_to_delete.append(point.id)
        
        if points_to_delete:
            qdrant_client.delete(
                collection_name=QDRANT_COLLECTION,
                points_selector=points_to_delete
            )
        
        return {
            "cv_id": cv_id,
            "deleted_points": len(points_to_delete),
            "status": "deleted"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete CV: {str(e)}")

@app.post("/map", response_model=CVMappingResult)
def map_cv_to_categories(request: CVMappingRequest):
    """
    Map CV content to role-specific categories using rule-based analysis
    
    Args:
        request: CV ID and role type for mapping
        
    Returns:
        Mapping result with detected and missing blocks
    """
    try:
        # Validate role type
        if request.role_type.lower() not in ["ba", "it"]:
            raise HTTPException(
                status_code=400, 
                detail="Invalid role_type. Supported: 'ba', 'it'"
            )
        
        # Get all chunks for this CV
        search_results = qdrant_client.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=1000
        )[0]
        
        # Filter chunks for the specified CV
        cv_chunks = []
        for point in search_results:
            if point.payload["cv_id"] == request.cv_id:
                cv_chunks.append(point.payload["chunk_text"])
        
        if not cv_chunks:
            raise HTTPException(
                status_code=404, 
                detail=f"CV with ID {request.cv_id} not found"
            )
        
        # Combine all chunks into full text
        full_text = "\n".join(cv_chunks)
        
        # Perform mapping analysis
        mapping_analysis = analyze_cv_mapping(full_text, request.role_type)
        
        return CVMappingResult(
            cv_id=request.cv_id,
            role_type=request.role_type,
            priority_level=mapping_analysis["priority_level"],
            detected_blocks=mapping_analysis["mapping_result"]["detected_blocks"],
            missing_blocks=mapping_analysis["mapping_result"]["missing_blocks"],
            total_categories=mapping_analysis["mapping_result"]["total_categories"],
            covered_categories=mapping_analysis["mapping_result"]["covered_categories"],
            recommendations=mapping_analysis["recommendations"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mapping failed: {str(e)}")

@app.get("/map/{cv_id}")
def map_cv_simple(cv_id: str, role_type: str = "ba"):
    """
    Simple mapping endpoint for admin UI
    
    Args:
        cv_id: CV identifier
        role_type: Role type ("ba" or "it")
        
    Returns:
        Simplified mapping result
    """
    try:
        # Validate role type
        if role_type.lower() not in ["ba", "it"]:
            raise HTTPException(
                status_code=400, 
                detail="Invalid role_type. Supported: 'ba', 'it'"
            )
        
        # Get all chunks for this CV
        search_results = qdrant_client.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=1000
        )[0]
        
        # Filter chunks for the specified CV
        cv_chunks = []
        for point in search_results:
            if point.payload["cv_id"] == cv_id:
                cv_chunks.append(point.payload["chunk_text"])
        
        if not cv_chunks:
            raise HTTPException(
                status_code=404, 
                detail=f"CV with ID {cv_id} not found"
            )
        
        # Combine all chunks into full text
        full_text = "\n".join(cv_chunks)
        
        # Perform mapping analysis
        mapping_analysis = analyze_cv_mapping(full_text, role_type)
        
        # Return simplified result
        return {
            "cv_id": cv_id,
            "role_type": role_type,
            "priority_level": mapping_analysis["priority_level"],
            "detected_blocks": {
                category: {
                    "status": data["status"],
                    "keyword_count": data["keyword_count"],
                    "coverage_score": round(data["coverage_score"], 2)
                }
                for category, data in mapping_analysis["mapping_result"]["detected_blocks"].items()
            },
            "missing_blocks": mapping_analysis["mapping_result"]["missing_blocks"],
            "coverage_summary": {
                "total_categories": mapping_analysis["mapping_result"]["total_categories"],
                "covered_categories": mapping_analysis["mapping_result"]["covered_categories"],
                "coverage_percentage": round(
                    (mapping_analysis["mapping_result"]["covered_categories"] / 
                     mapping_analysis["mapping_result"]["total_categories"]) * 100, 1
                )
            },
            "recommendations": mapping_analysis["recommendations"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mapping failed: {str(e)}")

@app.get("/stats")
def get_stats():
    """Get database statistics"""
    try:
        collection_info = qdrant_client.get_collection(QDRANT_COLLECTION)
        
        return {
            "collection_name": QDRANT_COLLECTION,
            "total_points": collection_info.points_count,
            "vector_size": collection_info.config.params.vectors.size,
            "distance_metric": collection_info.config.params.vectors.distance,
            "embedder_model": EMBEDDER_MODEL,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8007"))
    uvicorn.run(app, host="0.0.0.0", port=port)
