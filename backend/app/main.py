from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
import os
import zipfile
from pathlib import Path
from dotenv import load_dotenv
from app.version import get_version
from app.core.plugin_manager import get_plugin_manager
from app.api.routes import files, insights, analyze, errors

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_sample_files():
    """Extract sample files on first startup if not already extracted."""
    try:
        # Get backend directory (app/main.py -> app/ -> backend/)
        backend_dir = Path(__file__).parent.parent
        samples_dir = backend_dir / "samples"
        
        # Sample file paths
        zip_path = samples_dir / "android-bugreport.zip"
        txt_path = samples_dir / "android-bugreport.txt"
        
        # Check if sample directory and zip exist
        if not samples_dir.exists():
            logger.warning(f"Samples directory not found: {samples_dir}")
            return
        
        if not zip_path.exists():
            logger.warning(f"Sample zip file not found: {zip_path}")
            return
        
        # Extract if not already extracted
        if not txt_path.exists():
            logger.info(f"Extracting sample file: {zip_path.name}")
            logger.info(f"This may take a moment (extracting ~57MB)...")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extract only the .txt file, skip __MACOSX folder
                for member in zip_ref.namelist():
                    if member.endswith('.txt') and not member.startswith('__MACOSX'):
                        # Extract with original name then rename
                        extracted_path = samples_dir / member
                        zip_ref.extract(member, samples_dir)
                        
                        # Rename to simplified name if different
                        if extracted_path.name != txt_path.name:
                            extracted_path.rename(txt_path)
                        
                        file_size_mb = txt_path.stat().st_size / (1024 * 1024)
                        logger.info(f"✓ Sample file extracted: {txt_path.name} ({file_size_mb:.1f}MB)")
                        logger.info(f"✓ Sample file location: {txt_path}")
                        break
        else:
            file_size_mb = txt_path.stat().st_size / (1024 * 1024)
            logger.info(f"✓ Sample file ready: {txt_path.name} ({file_size_mb:.1f}MB)")
            logger.debug(f"  Location: {txt_path}")
    
    except Exception as e:
        logger.error(f"Failed to extract sample files: {e}", exc_info=True)

app = FastAPI(
    title="Lens API",
    description="A modular engine for extracting insights from messy data! - API for analyzing log files with plugin-based insights",
    version=get_version()
)

# Get configuration from environment variables
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:34000")
serve_frontend = os.getenv("SERVE_FRONTEND", "false").lower() in ("true", "1", "yes")

# CORS configuration
# In production when serving frontend from backend, CORS is less critical but keep for flexibility
if serve_frontend:
    # When serving frontend from backend, allow same origin and configured frontend URL
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins when serving frontend (same origin + flexibility)
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        max_age=3600,
    )
else:
    # Development mode: only allow configured frontend URL
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[frontend_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        max_age=3600,  # Cache preflight responses for 1 hour (reduces OPTIONS requests)
    )

# Register API routes
app.include_router(files.router)
app.include_router(insights.router)
app.include_router(analyze.router)
app.include_router(errors.router)


@app.on_event("startup")
async def startup_event():
    """Initialize plugin manager and discover insights on startup."""
    logger.info("Initializing plugin manager...")
    plugin_manager = get_plugin_manager()
    plugin_manager.discover_insights()
    logger.info(f"Discovered {len(plugin_manager.get_all_insights())} insights")
    
    # Check ripgrep availability
    from app.utils.ripgrep import is_ripgrep_available
    if is_ripgrep_available():
        logger.info("✓ Ripgrep is available for fast pattern matching (10-100x faster)")
    else:
        logger.warning("⚠ Ripgrep not found. Install for 10-100x faster pattern matching:")
        logger.warning("  - macOS: brew install ripgrep")
        logger.warning("  - Linux (Debian/Ubuntu): sudo apt-get install ripgrep")
        logger.warning("  - Linux (Fedora): sudo dnf install ripgrep")
        logger.warning("  - More info: https://github.com/BurntSushi/ripgrep#installation")
    
    # Extract sample files if needed
    extract_sample_files()


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


@app.get("/api/profiling")
async def profiling_status():
    """Get profiling status (whether profiling is enabled)."""
    profiling_enabled = os.getenv("ENABLE_PROFILING", "false").lower() in ("true", "1", "yes")
    return {"enabled": profiling_enabled}


@app.get("/api/hello")
async def hello():
    logger.info("Hello endpoint called")
    return {"message": "Hello from backend"}


# Serve frontend static files in production mode
if serve_frontend:
    # Get project root (backend/app/main.py -> backend/ -> root/)
    project_root = Path(__file__).parent.parent.parent
    frontend_out_dir = project_root / "frontend" / "out"
    
    if frontend_out_dir.exists():
        logger.info(f"Serving frontend static files from: {frontend_out_dir}")
        
        # Serve static assets (_next directory)
        if (frontend_out_dir / "_next").exists():
            app.mount("/_next", StaticFiles(directory=frontend_out_dir / "_next"), name="static")
        
        # Serve other static files (images, etc.) - use a catch-all for these
        # Individual routes for common static files
        @app.get("/favicon.ico")
        async def serve_favicon():
            favicon_path = frontend_out_dir / "favicon.ico"
            if favicon_path.exists():
                return FileResponse(favicon_path)
            raise HTTPException(status_code=404)
        
        # Catch-all route for SPA routing (must be last)
        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            # Don't serve API routes as static files
            if full_path.startswith("api/"):
                raise HTTPException(status_code=404, detail="API endpoint not found")
            
            # Serve index.html for all non-API routes (SPA routing)
            index_path = frontend_out_dir / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            else:
                raise HTTPException(status_code=404, detail="Frontend not found. Please build the frontend first.")
    else:
        logger.warning(f"Frontend output directory not found: {frontend_out_dir}")
        logger.warning("Frontend will not be served. Run 'npm run build' in frontend directory first.")
