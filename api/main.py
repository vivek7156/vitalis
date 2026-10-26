"""Vitalis FastAPI application entry point.

Scaffolds API endpoints with structured error handling, CORS, health checks,
and honest prototype readiness states per Section 4.3 and 14 of the checklist.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import health, screening

app = FastAPI(
    title="Vitalis Health Screening API",
    description=(
        "Explainable Agentic AI Framework for Multi-Disease Health-Risk Screening. "
        "Prototype Foundation and Module 1 Data Pipeline."
    ),
    version="0.1.0",
)

# Configure development CORS for explicitly allowed origins (T-PROTO-08)
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# Structured validation error handler (T-PROTO-01)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = []
    for err in exc.errors():
        loc = " -> ".join(str(p) for p in err.get("loc", []))
        details.append({
            "field": loc,
            "issue": err.get("msg", "Invalid value"),
        })
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Input validation failed. Missing or invalid required fields.",
            "details": details,
        },
    )


# Include route modules
app.include_router(health.router)
app.include_router(screening.router)


@app.get("/")
def root():
    return {
        "service": "Vitalis Screening API",
        "version": "0.1.0",
        "docs_url": "/docs",
        "health_url": "/health",
        "readiness_url": "/readiness",
    }
