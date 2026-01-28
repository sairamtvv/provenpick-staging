"""
Main FastAPI application entry point.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import articles, pipeline, archive

# Load environment variables (dotenv is optional)
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system environment variables

# Create FastAPI app
app = FastAPI(
    title="ProvenPick Staging API",
    description="Content staging and moderation system for ProvenPick",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(articles.router)
app.include_router(pipeline.router)
app.include_router(archive.router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "ProvenPick Staging API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Detailed health check"""
    try:
        # Test database connection using raw query
        from backend.db.connection import DB
        import asyncpg

        # Get a connection and run a simple query
        async with DB.connection_pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT COUNT(*) FROM staging.staging_article WHERE status = 'pending'"
            )

        return {
            "status": "healthy",
            "database": "connected",
            "pending_articles": result,
        }
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=True,
    )
