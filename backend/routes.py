from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
import io
import logging
import math

from model import forecast_demand
from alerts import generate_alerts
from utils import parse_csv  # Now contains only parsing logic

router = APIRouter()
logging.basicConfig(level=logging.INFO)

# ------------------ Inline Utility: Sanitize JSON ------------------
def sanitize_json(data):
    """Recursively convert NaN, inf, -inf to None for JSON-safe response."""
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

# ------------------ Health Check Endpoint ------------------
@router.get("/health")
async def health():
    return {"status": "OK"}

# ------------------ Predict Endpoint ------------------
@router.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    try:
        # Read uploaded file
        contents = await file.read()
        df = parse_csv(io.BytesIO(contents))

        logging.info(f"📥 Received file: {file.filename}")
        logging.info(f"📊 Parsed {len(df)} rows from uploaded CSV.")

        # Run forecast
        forecast_output = forecast_demand(df)

        if isinstance(forecast_output, dict):
            forecast_result_df = pd.DataFrame(forecast_output)
        elif isinstance(forecast_output, pd.DataFrame):
            forecast_result_df = forecast_output
        else:
            raise HTTPException(status_code=500, detail="forecast_demand() must return DataFrame or dict")

        # Validate required fields
        if "sku" not in df.columns or "sku" not in forecast_result_df.columns:
            raise HTTPException(status_code=400, detail="Missing 'sku' in input or forecast output")

        # Generate smart alerts
        alerts = generate_alerts(df, forecast_result_df)

        # Convert forecast results to JSON-safe dictionary
        forecast_result = forecast_result_df.to_dict(orient="records")

        return {
            "forecast": sanitize_json(forecast_result),
            "alerts": sanitize_json(alerts)
        }

    except Exception as e:
        logging.error(f"❌ Prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
