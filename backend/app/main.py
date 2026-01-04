from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000"],
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

