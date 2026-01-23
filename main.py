import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers.analyze import router as analyze_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("api")

app = FastAPI()

# CORS to allow Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request {request.method} {request.url}")
    try:
        response = await call_next(request)
    except Exception as e:
        logger.exception(f"Unhandled exception for {request.method} {request.url}: {e}")
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
    logger.info(f"Response status {response.status_code} for {request.method} {request.url}")
    return response

# Global exception handler for HTTPException is handled by FastAPI; add fallback for generic exceptions
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Exception on {request.method} {request.url}: {exc}")
    return JSONResponse(status_code=500, content={"detail": str(exc)})

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

# Mount analyzer API
app.include_router(analyze_router, prefix="", tags=["analyze"])
