from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from fastapi.routing import APIRouter

import logging
import pandas as pd
from io import StringIO
import math

from model import forecast_demand
from alerts import generate_alerts

# ---------------------- Setup FastAPI App ----------------------
app = FastAPI(
    title="AI Inventory Waste Reduction API",
    version="1.0.0",
    description="A FastAPI backend for demand forecasting and smart alerting."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ In production, lock this down
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------- Logging Setup ----------------------
logging.basicConfig(level=logging.INFO)

# ---------------------- Utility: JSON Sanitizer ----------------------
def sanitize_json(data):
    """Recursively clean JSON-unsafe values like NaN and Inf."""
    if isinstance(data, dict):
        return {k: sanitize_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_json(item) for item in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    else:
        return data

# ---------------------- Exception Handlers ----------------------
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

# ---------------------- Prediction Endpoint ----------------------
router = APIRouter()

@router.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df = pd.read_csv(StringIO(content.decode("utf-8")))

        required_cols = {"date", "sku", "sales", "inventory"}
        if not required_cols.issubset(df.columns):
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={"error": f"Missing required columns: {required_cols - set(df.columns)}"}
            )

        logging.info("📊 Running demand forecast model...")
        forecast_df = forecast_demand(df)

        # ✅ Calculate max predicted day per SKU
        max_idx = forecast_df.groupby("sku")["prediction"].idxmax()
        max_days = forecast_df.loc[max_idx, ["sku", "date"]].rename(columns={"date": "max_predicted_day"})
        forecast_df = pd.merge(forecast_df, max_days, on="sku", how="left")

        # ✅ Handle product_name mapping BEFORE alerts
        if "product_name" in df.columns:
            sku_name_map = df[["sku", "product_name"]].dropna().drop_duplicates().set_index("sku")["product_name"].to_dict()
            forecast_df["product_name"] = forecast_df["sku"].map(sku_name_map)
        else:
            forecast_df["product_name"] = "N/A"

        # ✅ Now generate alerts AFTER product_name is added
        logging.info("🚨 Generating alerts...")
        alerts = generate_alerts(df, forecast_df)

        # ✅ Merge forecast with actuals
        merged = pd.merge(
            forecast_df,
            df[["date", "sku", "sales", "inventory"]],
            on=["date", "sku"],
            how="left"
        )

        return {
            "forecast": sanitize_json(merged.to_dict(orient="records")),
            "alerts": sanitize_json(alerts)
        }

    except Exception as e:
        logging.exception("Error in /predict route")
        raise e

# ---------------------- Register Routes ----------------------
app.include_router(router)
