from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from dotenv import load_dotenv
from app.version import get_version
from app.core.plugin_manager import get_plugin_manager
from app.api.routes import files, insights, analyze

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Lens API",
    description="A modular engine for extracting insight from data - API for analyzing log files with plugin-based insights",
    version=get_version()
)

# Get configuration from environment variables
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:34000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(files.router)
app.include_router(insights.router)
app.include_router(analyze.router)


@app.on_event("startup")
async def startup_event():
    """Initialize plugin manager and discover insights on startup."""
    logger.info("Initializing plugin manager...")
    plugin_manager = get_plugin_manager()
    plugin_manager.discover_insights()
    logger.info(f"Discovered {len(plugin_manager.get_all_insights())} insights")


@app.get("/api/health")
async def health():
    logger.info("Health check requested")
    return {"status": "ok"}


@app.get("/api/version")
async def version():
    """Get the application version."""
    version_str = get_version()
    logger.info(f"Version endpoint called: {version_str}")
    return {"version": version_str}


@app.get("/api/hello")
async def hello():
    logger.info("Hello endpoint called")
    return {"message": "Hello from backend"}
