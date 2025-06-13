import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="AI Inventory Optimizer", layout="centered")

st.title("📦 AI-Powered Inventory Waste Reduction")

# Upload CSV
uploaded_file = st.file_uploader("Upload your inventory CSV", type="csv")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.success("✅ CSV uploaded successfully!")
        st.dataframe(df.head(10))

        # Send to backend
        with st.spinner("⏳ Sending data to AI backend..."):
            uploaded_file.seek(0)  # Important: reset file pointer
            response = requests.post(
                "http://localhost:8000/predict",  # 🔁 Update this if deployed
                files={"file": uploaded_file}
            )

            if response.status_code == 200:
                result = response.json()
                st.success("✅ Forecast and Alerts Received!")

                for sku_block in result["alerts"]:
                    sku = sku_block["sku"]
                    st.subheader(f"🔍 SKU: {sku}")
                    st.markdown(f"**Product Name**: {sku_block.get('product_name', 'N/A')}")
                    st.markdown(f"**Forecast Window**: {sku_block['forecast_window']}")
                    st.markdown(f"**Avg. Prediction**: `{sku_block['avg_prediction']}`")
                    st.markdown(f"**Max Predicted Day**: `{sku_block['max_predicted_day']}`")

                    for alert in sku_block["alerts"]:
                        severity = alert.get("severity", "Low")
                        severity_icon = {
                            "High": "🔴",
                            "Medium": "🟠",
                            "Low": "🟢"
                        }.get(severity, "⚪")
                        st.markdown(f"{severity_icon} **{alert['type']}**: {alert['message']}")
            else:
                st.error(f"❌ Backend Error: {response.status_code} - {response.text}")

    except Exception as e:
        st.error(f"⚠️ Error parsing CSV: {str(e)}")
