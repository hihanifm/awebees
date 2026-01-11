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
from app.core.config import AppConfig
from app.api.routes import files, insights, analyze, errors, insight_paths, playground, logging as logging_routes, logs, help

load_dotenv()

log_level = getattr(logging, AppConfig.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)


def extract_sample_files():
    try:
        # Get backend directory (app/main.py -> app/ -> backend/)
        backend_dir = Path(__file__).parent.parent
        samples_dir = backend_dir / "samples"
        
        # Extract built-in samples
        zip_path = samples_dir / "android-bugreport.zip"
        txt_path = samples_dir / "android-bugreport.txt"
        
        # Check if sample directory and zip exist
        if not samples_dir.exists():
            logger.warning(f"Samples directory not found: {samples_dir}")
        elif zip_path.exists():
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
        
        # Extract samples from external insight paths
        # This will trigger extraction during discovery
        from app.core.sample_discovery import discover_all_samples
        logger.info("Discovering and extracting samples from external insight paths...")
        all_samples = discover_all_samples()
        logger.info(f"Sample extraction complete. Total samples available: {len(all_samples)}")
    
    except Exception as e:
        logger.error(f"Failed to extract sample files: {e}", exc_info=True)

app = FastAPI(
    title="Lens API",
    description="A modular engine for extracting insights from messy data! - API for analyzing log files with plugin-based insights",
    version=get_version()
)

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:34000")
serve_frontend = os.getenv("SERVE_FRONTEND", "false").lower() in ("true", "1", "yes")

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
        max_age=3600,
    )

app.include_router(files.router)
app.include_router(insights.router)
app.include_router(analyze.router)
app.include_router(errors.router)
app.include_router(insight_paths.router)
app.include_router(playground.router)
app.include_router(logging_routes.router)
app.include_router(logs.router)
app.include_router(help.router)


@app.on_event("startup")
async def startup_event():
    logger.info("Initializing plugin manager...")
    plugin_manager = get_plugin_manager()
    
    # Discover insights from all sources (built-in + external)
    plugin_manager.discover_all_insights()
    
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


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")
    logger.info("Shutdown complete")


@app.get("/api/health")
async def health():
    logger.info("Health check requested")
    return {"status": "ok"}


@app.get("/api/version")
async def version():
    version_str = get_version()
    logger.info(f"Version endpoint called: {version_str}")
    return {"version": version_str}


@app.get("/api/profiling")
async def profiling_status():
    profiling_enabled = os.getenv("ENABLE_PROFILING", "false").lower() in ("true", "1", "yes")
    return {"enabled": profiling_enabled}


@app.get("/api/hello")
async def hello():
    logger.info("Hello endpoint called")
    return {"message": "Hello from backend"}


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
        # Support both GET and HEAD methods
        @app.api_route("/favicon.ico", methods=["GET", "HEAD"])
        async def serve_favicon():
            favicon_path = frontend_out_dir / "favicon.ico"
            if favicon_path.exists():
                return FileResponse(favicon_path)
            raise HTTPException(status_code=404)
        
        # Catch-all route for serving Next.js static export (must be last)
        # Support both GET and HEAD methods (HEAD is used by Next.js prefetching)
        @app.api_route("/{full_path:path}", methods=["GET", "HEAD"])
        async def serve_frontend(full_path: str):
            # Don't serve API routes as static files
            if full_path.startswith("api/"):
                raise HTTPException(status_code=404, detail="API endpoint not found")
            
            # For Next.js static export, try to serve the actual HTML file first
            # e.g., /playground -> playground.html
            if full_path:
                # Try with .html extension
                html_path = frontend_out_dir / f"{full_path}.html"
                if html_path.exists():
                    return FileResponse(html_path)
                
                # Try as directory with index.html
                dir_index_path = frontend_out_dir / full_path / "index.html"
                if dir_index_path.exists():
                    return FileResponse(dir_index_path)
                
                # Try serving the file directly (for images, etc.)
                direct_file_path = frontend_out_dir / full_path
                if direct_file_path.exists() and direct_file_path.is_file():
                    return FileResponse(direct_file_path)
            
            # Fallback to index.html for root and unknown routes
            index_path = frontend_out_dir / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            else:
                raise HTTPException(status_code=404, detail="Frontend not found. Please build the frontend first.")
    else:
        logger.warning(f"Frontend output directory not found: {frontend_out_dir}")
        logger.warning("Frontend will not be served. Run 'npm run build' in frontend directory first.")
