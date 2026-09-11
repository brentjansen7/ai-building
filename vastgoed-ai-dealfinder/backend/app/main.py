from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import time

from app.config import settings
from app.api.routes import router as api_router
from app.database import engine, Base

logger = structlog.get_logger()

app = FastAPI(
    title="Vastgoed AI Dealfinder",
    description="API voor het detecteren van ondergewaardeerde kluswoningen in Nederland",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS voor Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In productie: restrict naar extension origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(duration * 1000, 2),
    )
    return response


@app.on_event("startup")
async def startup():
    logger.info("Starting Vastgoed AI Dealfinder API")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down API")
    await engine.dispose()


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


app.include_router(api_router, prefix="/api")
