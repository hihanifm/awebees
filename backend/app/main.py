from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Get configuration from environment variables
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    logger.info("Health check requested")
    return {"status": "ok"}


@app.get("/api/hello")
async def hello():
    logger.info("Hello endpoint called")
    return {"message": "Hello from backend"}
