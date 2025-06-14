import streamlit as st
import pandas as pd
import requests

# ------------------ Page Config ------------------
st.set_page_config(page_title="AI Inventory Optimizer", layout="centered")
st.title("📦 AI-Powered Inventory Waste Reduction")

# ------------------ Sidebar Navigation ------------------
page = st.sidebar.radio("Navigate", ["📊 Dashboard", "📈 SKU Comparison"])

# ------------------ Upload Section ------------------
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None

uploaded_file = st.file_uploader("📤 Upload your inventory CSV", type="csv")

if uploaded_file is not None:
    st.session_state.uploaded_file = uploaded_file

    try:
        df = pd.read_csv(uploaded_file)
        st.success("✅ CSV uploaded successfully!")
        st.dataframe(df.head(10))

        with st.spinner("⏳ Sending data to AI backend..."):
            uploaded_file.seek(0)
            try:
                response = requests.post(
                    "http://localhost:8000/predict",
                    files={"file": uploaded_file},
                    timeout=60  # 🧠 avoid infinite wait
                )
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Failed to connect to backend: {e}")
                response = None

        if response and response.status_code == 200:
            result = response.json()
            st.success("✅ Forecast and Alerts Received!")
            st.session_state.forecast_data = result.get('forecast', [])
            st.session_state.alerts_data = result.get('alerts', [])
        elif response:
            st.error(f"❌ Backend Error: {response.status_code} - {response.text}")

    except Exception as e:
        st.error(f"⚠️ Error processing CSV: {str(e)}")

# ------------------ Dashboard Page ------------------
def render_dashboard():
    alerts_data = st.session_state.get('alerts_data')
    if alerts_data:
        for sku_block in alerts_data:
            sku = sku_block.get("sku", "N/A")
            product_name = sku_block.get("product_name", "N/A")
            st.subheader(f"🔍 SKU: {sku}")
            st.markdown(f"**Product Name**: {product_name}")
            st.markdown(f"**Forecast Window**: {sku_block.get('forecast_window', 'N/A')}")
            st.markdown(f"**Avg. Prediction**: `{sku_block.get('avg_prediction', 'N/A')}`")
            st.markdown(f"**Max Predicted Day**: `{sku_block.get('max_predicted_day', 'N/A')}`")

            for alert in sku_block.get("alerts", []):
                severity = alert.get("severity", "Low")
                severity_icon = {
                    "High": "🔴",
                    "Medium": "🟠",
                    "Low": "🟢"
                }.get(severity, "⚪")
                st.markdown(f"{severity_icon} **{alert.get('type', 'Alert')}**: {alert.get('message', 'No details available')}")
    else:
        st.info("📤 Please upload a CSV and run the prediction to view dashboard insights.")

# ------------------ SKU Comparison Page ------------------
def render_sku_comparison():
    forecast_data = st.session_state.get('forecast_data')
    if forecast_data:
        st.header("📈 SKU Inventory vs Sales Comparison")
        forecast_df = pd.DataFrame(forecast_data)

        required_cols = {'sku', 'inventory', 'sales', 'date'}
        if required_cols.issubset(forecast_df.columns):
            available_skus = forecast_df["sku"].dropna().unique().tolist()
            selected_sku = st.selectbox("Select SKU for Visualization", available_skus)

            product_name = forecast_df[forecast_df["sku"] == selected_sku]["product_name"].dropna().unique()
            product_name = product_name[0] if len(product_name) > 0 else "N/A"
            st.markdown(f"**Product Name**: {product_name}")

            chart_data = forecast_df[forecast_df["sku"] == selected_sku][["date", "inventory", "sales"]].copy()
            chart_data["date"] = pd.to_datetime(chart_data["date"])
            chart_data.set_index("date", inplace=True)

            st.line_chart(chart_data)
        else:
            st.warning(f"⚠️ Required columns {required_cols} not found in forecast data.")
    else:
        st.info("📤 Please upload a CSV and run the prediction to see the comparison chart.")

# ------------------ Page Router ------------------
if page == "📊 Dashboard":
    render_dashboard()
elif page == "📈 SKU Comparison":
    render_sku_comparison()
