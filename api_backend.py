#!/usr/bin/env python3
"""
FastAPI Backend for Bangladesh Job Search Agent
Converts Streamlit functionality to API endpoints
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from src.core.rag_engine import RAGEngine
from src.core.query_parser import QueryParser
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_job_to_dict(job) -> Dict[str, Any]:
    """Convert JobData object to dictionary for JSON serialization"""
    if hasattr(job, '__dict__'):
        job_dict = job.__dict__.copy()
        # Convert datetime objects to strings
        if 'posted_date' in job_dict and job_dict['posted_date']:
            job_dict['posted_date'] = str(job_dict['posted_date'])
        # Map description to summary for QA compatibility
        if 'description' in job_dict and job_dict['description']:
            job_dict['summary'] = job_dict['description']
        # Add source information
        job_dict['source'] = 'LinkedIn Database'
        return job_dict
    else:
        # If it's already a dict, just add source and map description to summary
        job_dict = job.copy() if isinstance(job, dict) else {}
        if 'description' in job_dict and job_dict['description']:
            job_dict['summary'] = job_dict['description']
        job_dict['source'] = job_dict.get('source', 'Web Search')
        return job_dict

# Initialize FastAPI app
app = FastAPI(
    title="Bangladesh Job Search API",
    description="AI-Powered Job Search API with RAG Engine",
    version="1.0.0"
)

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=False,  # Changed to False for testing
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize core components
try:
    rag_engine = RAGEngine()
    query_parser = QueryParser()
    config = Config()
    logger.info("✅ Core components initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize core components: {e}")
    rag_engine = None
    query_parser = None
    config = None

# Pydantic models for API requests/responses
class JobSearchRequest(BaseModel):
    query: str
    location: Optional[str] = "All Locations"
    experience: Optional[str] = "Any"
    job_type: Optional[str] = "Any"
    salary_range: Optional[tuple] = (0, 200000)
    sources: Optional[Dict[str, bool]] = {
        "Database": True,
        "Web Search": True
    }
    max_results: Optional[int] = 20
    timeout: Optional[int] = 30

class JobSearchResponse(BaseModel):
    success: bool
    jobs: List[Dict[str, Any]]
    total_found: int
    search_time: float
    sources_used: List[str]
    message: str
    is_relevant: Optional[bool] = True
    is_inappropriate: Optional[bool] = False
    suggestions: Optional[List[str]] = []
    database_jobs: int = 0
    web_search_jobs: int = 0

class HealthResponse(BaseModel):
    status: str
    components: Dict[str, str]
    timestamp: str

# API Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Bangladesh Job Search API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    components = {}
    
    # Check RAG engine
    if rag_engine:
        components["rag_engine"] = "✅ Healthy"
    else:
        components["rag_engine"] = "❌ Failed"
    
    # Check query parser
    if query_parser:
        components["query_parser"] = "✅ Healthy"
    else:
        components["query_parser"] = "❌ Failed"
    
    # Check config
    if config:
        components["config"] = "✅ Healthy"
    else:
        components["config"] = "❌ Failed"
    
    return HealthResponse(
        status="healthy" if all("✅" in status for status in components.values()) else "unhealthy",
        components=components,
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/search", response_model=JobSearchResponse)
async def search_jobs(request: JobSearchRequest):
    """Search for jobs using the enhanced RAG engine"""
    try:
        if not rag_engine:
            raise HTTPException(status_code=500, detail="RAG engine not initialized")
        
        logger.info(f"🔍 Processing job search: {request.query}")
        
        # Search using enhanced RAG engine
        start_time = datetime.now()
        results = rag_engine.search(request.query)
        search_time = (datetime.now() - start_time).total_seconds()
        
        # Check if query was relevant
        if not results.get("is_relevant", True):
            logger.info("❌ Query was not job-related")
            return JobSearchResponse(
                success=False,
                jobs=[],
                total_found=0,
                search_time=search_time,
                sources_used=[],
                message=results.get("summary", "I'm a job search assistant."),
                is_relevant=False,
                is_inappropriate=results.get("is_inappropriate", False),
                suggestions=results.get("suggestions", []),
                database_jobs=0,
                web_search_jobs=0
            )
        
        # Process jobs
        jobs = results.get('jobs', [])
        if jobs:
            # Convert JobData objects to dictionaries
            processed_jobs = []
            for job in jobs:
                job_dict = convert_job_to_dict(job)
                processed_jobs.append(job_dict)
            
            total_found = len(processed_jobs)
            sources_used = list(set(job.get('source', 'Unknown') for job in processed_jobs))
            
            logger.info(f"✅ Found {total_found} jobs in {search_time:.2f}s")
            
            return JobSearchResponse(
                success=True,
                jobs=processed_jobs,
                total_found=total_found,
                search_time=search_time,
                sources_used=sources_used,
                message=results.get("summary", f"Found {total_found} jobs matching your criteria"),
                is_relevant=True,
                is_inappropriate=False,
                suggestions=[],
                database_jobs=results.get("database_jobs", 0),
                web_search_jobs=results.get("web_search_jobs", 0)
            )
        else:
            logger.warning("❌ No jobs found")
            return JobSearchResponse(
                success=False,
                jobs=[],
                total_found=0,
                search_time=search_time,
                sources_used=[],
                message=results.get("summary", "No jobs found. Try adjusting your search criteria."),
                is_relevant=True,
                is_inappropriate=False,
                suggestions=[],
                database_jobs=results.get("database_jobs", 0),
                web_search_jobs=results.get("web_search_jobs", 0)
            )
            
    except Exception as e:
        logger.error(f"❌ Error during job search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/filters")
async def get_filters():
    """Get available filters and options"""
    return {
        "locations": [
            "All Locations", "Dhaka", "Chittagong", "Sylhet", 
            "Rajshahi", "Khulna", "Barisal", "Rangpur", "Mymensingh"
        ],
        "experience_levels": [
            "Any", "Entry Level", "Mid Level", "Senior Level", "Executive"
        ],
        "job_types": [
            "Any", "Full-time", "Part-time", "Contract", "Remote", "Hybrid"
        ],
        "data_sources": [
            "Database", "Web Search"
        ],
        "salary_ranges": {
            "min": 0,
            "max": 200000,
            "step": 5000
        }
    }

@app.get("/api/stats")
async def get_stats():
    """Get system statistics and performance metrics"""
    try:
        if rag_engine and rag_engine.job_database:
            db_stats = rag_engine.job_database.get_statistics()
            return {
                "database": {
                    "total_jobs": db_stats.get('total_jobs', 0),
                    "unique_companies": db_stats.get('unique_companies', 0),
                    "unique_locations": db_stats.get('unique_locations', 0),
                    "unique_job_types": db_stats.get('unique_job_types', 0),
                    "recent_jobs": db_stats.get('recent_jobs', 0)
                },
                "system": {
                    "rag_engine_status": "✅ Active" if rag_engine else "❌ Inactive",
                    "query_parser_status": "✅ Active" if query_parser else "❌ Inactive",
                    "web_search_status": "✅ Available",
                    "quality_assurance": "✅ Active"
                },
                "features": [
                    "Intelligent Query Understanding",
                    "Professional Response Handling",
                    "Database-First Search",
                    "Web Search Fallback",
                    "Quality Assurance"
                ],
                "last_updated": datetime.now().isoformat()
            }
        else:
            return {
                "error": "Database not available",
                "system": {
                    "rag_engine_status": "❌ Inactive",
                    "query_parser_status": "❌ Inactive"
                },
                "last_updated": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return {"error": str(e), "last_updated": datetime.now().isoformat()}

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "timestamp": datetime.now().isoformat()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "timestamp": datetime.now().isoformat()}
    )

def start_api_server():
    """Start the FastAPI server"""
    try:
        logger.info("🚀 Starting Bangladesh Job Search API...")
        uvicorn.run(
            "api_backend:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"❌ Failed to start API server: {e}")

if __name__ == "__main__":
    start_api_server()
