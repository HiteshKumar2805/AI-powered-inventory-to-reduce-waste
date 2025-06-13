# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from fastapi.responses import JSONResponse

import logging
from routes import router  # 🔁 Import routes from separate file

# ----------------------------- Logging Setup -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ----------------------------- App Setup -----------------------------
app = FastAPI(
    title="AI Inventory Waste Reduction API",
    version="1.0.0",
    description="A FastAPI backend for demand forecasting and smart alerting."
)

# ----------------------------- CORS Middleware -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for dev; tighten for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------- Global Exception Handlers -----------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logging.warning(f"Validation error on request {request.url}: {exc}")
    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content={"error": "Validation Error", "details": exc.errors()},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logging.error(f"Unhandled error on {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": str(exc)},
    )

# ----------------------------- Route Registration -----------------------------
app.include_router(router)
