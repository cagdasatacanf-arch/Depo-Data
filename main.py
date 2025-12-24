"""
Depo - Historical Commodity Data API
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from api.routes import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Depo API",
    description="Historical commodity and stock price data API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for Lovable frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "http://localhost:5173",  # Vite default port
        "http://localhost:8080",  # Alternative local port
        "*"  # Allow all origins (restrict in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("Starting Depo API...")
    logger.info("Preloading data...")
    
    try:
        from data.loader import DataLoader
        loader = DataLoader()
        loader.load_data()
        commodities = loader.get_commodities()
        logger.info(f"Loaded {len(commodities)} commodities")
        logger.info("Data preload complete")
    except Exception as e:
        logger.error(f"Error preloading data: {e}")
        logger.warning("API will attempt to load data on first request")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Shutting down Depo API...")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Depo API",
        "version": "1.0.0",
        "description": "Historical commodity and stock price data API",
        "phase": "Phase 1: Closed System (Existing Data Only)",
        "docs": "/docs",
        "health": "/api/health",
        "endpoints": {
            "commodities": "/api/commodities",
            "history": "/api/commodities/{name}/history",
            "compare": "/api/commodities/compare?names=Gold,Silver",
            "statistics": "/api/stats/{name}",
            "date_range": "/api/date-range"
        }
    }


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={"error": "Resource not found", "detail": str(exc.detail) if hasattr(exc, 'detail') else None}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "Please check server logs"}
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Uvicorn server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
