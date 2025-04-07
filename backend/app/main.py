import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.api.api import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.db.session import engine
from app.db.base import Base

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_URL = os.getenv("DATABASE_URL")

APP_HOME = os.path.dirname(__file__) + "/../../"

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables, initialize resources, etc.
    if settings.AUTO_CREATE_TABLES:
        async with engine.begin() as conn:
            # In production, use Alembic for migrations instead
            await conn.run_sync(Base.metadata.create_all)
    
    print("Application startup complete")
    
    yield  # This is where the application runs
    
    # Shutdown: Close connections, cleanup resources
    print("Application shutdown")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Rockwell Twitter-like Feed Research Platform API",
    version="1.0.0",
    docs_url="/api/docs" if settings.SHOW_DOCS else None,
    redoc_url="/api/redoc" if settings.SHOW_DOCS else None,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware for request timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Global exception handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": format_validation_errors(exc.errors())},
    )

# Format validation errors to be more readable
def format_validation_errors(errors):
    formatted_errors = []
    for error in errors:
        formatted_errors.append({
            "loc": " -> ".join(str(loc) for loc in error["loc"]),
            "msg": error["msg"],
            "type": error["type"],
        })
    return formatted_errors

# Root endpoint for health check
@app.get("/", tags=["status"])
async def root():
    return {"status": "ok", "service": settings.PROJECT_NAME}

# Include API router with all endpoints
app.include_router(api_router, prefix="/api")

# Development server entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=settings.DEBUG
    )