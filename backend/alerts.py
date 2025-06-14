import pandas as pd
from datetime import datetime
import holidays

# Load Indian holidays
india_holidays = holidays.CountryHoliday("IN")

def generate_alerts(original_df: pd.DataFrame, forecast_df: pd.DataFrame):
    alerts = []

    # ✅ Validate necessary columns in both dataframes
    required_forecast_cols = {"sku", "date", "prediction"}
    required_original_cols = {"sku", "date", "inventory", "sales"}

    if not required_forecast_cols.issubset(forecast_df.columns):
        raise ValueError(f"Forecast DataFrame missing required columns: {required_forecast_cols - set(forecast_df.columns)}")

    if not required_original_cols.issubset(original_df.columns):
        raise ValueError(f"Original DataFrame missing required columns: {required_original_cols - set(original_df.columns)}")

    # ✅ Preprocess forecast_df
    forecast_df = forecast_df.copy()
    forecast_df['date'] = pd.to_datetime(forecast_df['date'])

    # Add holiday context
    forecast_df['is_holiday'] = forecast_df['date'].apply(lambda x: int(x in india_holidays))
    forecast_df['holiday_name'] = forecast_df['date'].apply(lambda x: india_holidays.get(x) if x in india_holidays else None)

    grouped = forecast_df.groupby('sku')

    for sku, group in grouped:
        sku_alerts = []
        group_sorted = group.sort_values(by='date')

        predictions = group_sorted['prediction'].tolist()
        dates = group_sorted['date'].dt.strftime('%Y-%m-%d').tolist()
        avg_prediction = sum(predictions) / len(predictions) if predictions else 0
        max_pred_day = dates[predictions.index(max(predictions))] if predictions else "N/A"
        forecast_window = f"{dates[0]} to {dates[-1]}" if dates else "N/A"

        holidays_in_window = group_sorted[group_sorted["is_holiday"] == 1]["holiday_name"].dropna().unique().tolist()
        holiday_context = f"(Holiday: {', '.join(holidays_in_window)})" if holidays_in_window else ""

        # 🆕 Get product_name (defensive fetch)
        product_name = "N/A"
        if "product_name" in group_sorted.columns:
            non_null_names = group_sorted["product_name"].dropna().unique()
            if len(non_null_names) > 0:
                product_name = non_null_names[0]

        # 🟠 Replenishment Alert
        if avg_prediction < 3 and not any(group_sorted['is_holiday']):
            sku_alerts.append({
                "type": "Replenishment Required",
                "severity": "High",
                "message": f"Demand for {sku} is low {holiday_context}. Consider replenishing."
            })

        # 🔴 Zero Demand
        if all(p == 0 for p in predictions) and not any(group_sorted['is_holiday']):
            sku_alerts.append({
                "type": "Zero Demand",
                "severity": "Critical",
                "message": f"No demand predicted for {sku} {holiday_context}. Investigate cause."
            })

        # 🟡 Slow-Moving Stock
        elif all(p <= 2 for p in predictions) and not all(p == 0 for p in predictions):
            sku_alerts.append({
                "type": "Slow-Moving Stock",
                "severity": "Low",
                "message": f"{sku} is moving slowly {holiday_context}. Monitor performance."
            })

        # 🟣 Overstock Risk
        if max(predictions) > 10:
            severity = "Low" if holidays_in_window else "Medium"
            sku_alerts.append({
                "type": "Overstock Risk",
                "severity": severity,
                "message": f"{sku} has high predicted stock {holiday_context}—possible overstock."
            })

        # 🔻 Consistent Decline
        if predictions == sorted(predictions, reverse=True) and len(set(predictions)) > 1:
            sku_alerts.append({
                "type": "Consistent Decline",
                "severity": "Medium",
                "message": f"{sku} shows a consistent decline in demand {holiday_context}."
            })

        # 🔁 Inventory vs Sales Delta Check
        original_sku_df = original_df[(original_df["sku"] == sku)]
        if not original_sku_df.empty:
            original_sku_df['date'] = pd.to_datetime(original_sku_df['date'])
            latest_row = original_sku_df.sort_values(by="date").iloc[-1]
            inv = latest_row["inventory"]
            sales = latest_row["sales"]

            if inv > 1.5 * sales:
                sku_alerts.append({
                    "type": "Stockpile Alert",
                    "severity": "Medium",
                    "message": f"Inventory ({inv}) significantly exceeds recent sales ({sales}). Risk of overstock."
                })

        # Append all alerts with product_name now included
        alerts.append({
            "sku": sku,
            "product_name": product_name,
            "forecast_window": forecast_window,
            "avg_prediction": round(avg_prediction, 2),
            "max_predicted_day": max_pred_day,
            "alerts": sku_alerts
        })

    return alerts
