from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
import io
import logging

from model import forecast_demand
from alerts import generate_alerts
from utils import parse_csv

router = APIRouter()
logging.basicConfig(level=logging.INFO)

@router.get("/health")
async def health():
    return {"status": "OK"}

@router.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    try:
        contents = await file.read()
        df = parse_csv(io.BytesIO(contents))

        logging.info(f"Received file: {file.filename}")
        logging.info(f"Parsed {len(df)} rows from uploaded CSV.")

        forecast_output = forecast_demand(df)

        if isinstance(forecast_output, dict):
            forecast_result_df = pd.DataFrame(forecast_output)
        elif isinstance(forecast_output, pd.DataFrame):
            forecast_result_df = forecast_output
        else:
            raise HTTPException(status_code=500, detail="forecast_demand() must return DataFrame or dict")

        if "sku" not in df.columns or "sku" not in forecast_result_df.columns:
            raise HTTPException(status_code=400, detail="Missing 'sku' in input or forecast output")

        alerts = generate_alerts(df, forecast_result_df)
        forecast_result = forecast_result_df.to_dict(orient="records")

        return {
            "forecast": forecast_result,
            "alerts": alerts
        }

    except Exception as e:
        logging.error(f"Prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
