import pandas as pd
from datetime import datetime

def generate_alerts(original_df: pd.DataFrame, forecast_df: pd.DataFrame):
    alerts = []
    forecast_df['date'] = pd.to_datetime(forecast_df['date'])

    grouped = forecast_df.groupby('sku')

    for sku, group in grouped:
        sku_alerts = []
        group_sorted = group.sort_values(by='date')
        predictions = group_sorted['prediction'].tolist()
        dates = group_sorted['date'].dt.strftime('%Y-%m-%d').tolist()

        avg_prediction = sum(predictions) / len(predictions) if predictions else 0
        max_pred_day = dates[predictions.index(max(predictions))] if predictions else "N/A"
        forecast_window = f"{dates[0]} to {dates[-1]}" if dates else "N/A"

        # Alert rules
        if avg_prediction < 3:
            sku_alerts.append({
                "type": "Replenishment Required",
                "severity": "High",
                "message": f"Demand for {sku} is low. Consider replenishing stock."
            })

        if all(p == 0 for p in predictions):
            sku_alerts.append({
                "type": "Zero Demand",
                "severity": "Critical",
                "message": f"No demand predicted for {sku}. Investigate cause."
            })

        elif all(p <= 2 for p in predictions):
            sku_alerts.append({
                "type": "Slow-Moving Stock",
                "severity": "Low",
                "message": f"{sku} is moving slowly. Monitor performance."
            })

        if max(predictions) > 10:
            sku_alerts.append({
                "type": "Overstock Risk",
                "severity": "Medium",
                "message": f"{sku} has high predicted stock—possible overstock."
            })

        if predictions == sorted(predictions, reverse=True) and len(set(predictions)) > 1:
            sku_alerts.append({
                "type": "Consistent Decline",
                "severity": "Medium",
                "message": f"{sku} shows a consistent decline in demand."
            })

        alerts.append({
            "sku": sku,
            "forecast_window": forecast_window,
            "avg_prediction": round(avg_prediction, 2),
            "max_predicted_day": max_pred_day,
            "alerts": sku_alerts
        })

    return alerts
