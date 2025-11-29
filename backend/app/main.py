"""
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.logger import get_logger
from app.core.error_middleware import ErrorLoggingMiddleware
from app.api.endpoints import market_data, analysis, alerts, websocket, news, backtest, risk_management, client_errors

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-powered trading analysis system",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Error logging middleware (must be added after other middleware)
app.add_middleware(ErrorLoggingMiddleware)

# Include routers
app.include_router(
    market_data.router,
    prefix="/api/v1/market",
    tags=["market"]
)
app.include_router(
    analysis.router,
    prefix="/api/v1/analysis",
    tags=["analysis"]
)
app.include_router(
    alerts.router,
    prefix="/api/v1/alerts",
    tags=["alerts"]
)
app.include_router(
    websocket.router,
    tags=["websocket"]
)
app.include_router(
    news.router,
    prefix="/api/v1/news",
    tags=["news"]
)
app.include_router(
    backtest.router,
    prefix="/api/v1/backtest",
    tags=["backtest"]
)
app.include_router(
    risk_management.router,
    prefix="/api/v1/risk",
    tags=["risk_management"]
)
app.include_router(
    client_errors.router,
    prefix="/api/v1/errors",
    tags=["errors"]
)


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info(f"Docs available at: http://localhost:8000/api/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Shutting down AI Trading System")


@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "message": "AI Trading System API",
        "version": settings.VERSION,
        "docs": "/api/docs"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.RELOAD
    )
