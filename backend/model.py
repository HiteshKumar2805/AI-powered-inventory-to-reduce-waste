import pandas as pd
from prophet import Prophet
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def forecast_demand(df: pd.DataFrame) -> pd.DataFrame:
    result_frames = []

    try:
        df["date"] = pd.to_datetime(df["date"])
    except Exception as e:
        logger.error(f"❌ Failed to parse 'date' column: {e}")
        raise ValueError("Invalid date format in input data.")

    for sku in df["sku"].unique():
        logger.info(f"📊 Forecasting for SKU: {sku}")

        sku_df = df[df["sku"] == sku]

        # Prophet needs 'ds' and 'y' columns
        try:
            sales_df = sku_df[["date", "sales"]].rename(columns={"date": "ds", "sales": "y"})
        except KeyError as ke:
            logger.error(f"⚠️ Missing required columns in input data: {ke}")
            continue

        if sales_df["y"].sum() == 0 or len(sales_df) < 2:
            logger.warning(f"⛔ Skipping SKU '{sku}' due to insufficient data.")
            continue

        try:
            model = Prophet(daily_seasonality=True)
            model.fit(sales_df)

            future = model.make_future_dataframe(periods=7)
            forecast = model.predict(future)

            forecast_result = forecast[["ds", "yhat"]].rename(columns={"ds": "date", "yhat": "prediction"})
            forecast_result["sku"] = sku
            result_frames.append(forecast_result)

            logger.info(f"✅ Forecast complete for SKU: {sku}")

        except Exception as e:
            logger.error(f"❌ Forecasting failed for SKU '{sku}': {e}")
            continue

    if result_frames:
        final_df = pd.concat(result_frames, ignore_index=True)
        logger.info(f"📈 Forecasting complete for {len(result_frames)} SKUs.")
        return final_df
    else:
        logger.warning("⚠️ No forecast results generated.")
        return pd.DataFrame(columns=["date", "prediction", "sku"])
