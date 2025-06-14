import streamlit as st
import pandas as pd
import requests
from streamlit_lottie import st_lottie
import json

# ------------------ Page Config ------------------
st.set_page_config(page_title="AI Inventory Optimizer", layout="wide")
st.markdown("""
    <style>
    .main {background-color: #F8F9FA;}
    .block-container {padding-top: 2rem;}
    </style>
""", unsafe_allow_html=True)

# ------------------ Sidebar Navigation ------------------
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Go to", ["📤 Upload CSV", "📊 Dashboard", "📈 SKU Comparison"])

# ------------------ Upload Page ------------------
def upload_page():
    st.title("AI Inventory Optimizer")
    st.title("📤 Upload Your Inventory CSV")
    st.markdown("Upload your inventory dataset to generate AI-powered forecasts and alerts.")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        try:
            df = pd.read_csv(uploaded_file)
            st.success("✅ CSV uploaded successfully!")
            st.dataframe(df.head(10), use_container_width=True)

            with st.spinner("⏳ Processing with AI engine..."):
                uploaded_file.seek(0)
                response = requests.post(
                    "http://localhost:8000/predict",
                    files={"file": uploaded_file},
                    timeout=60
                )

            if response.status_code == 200:
                result = response.json()
                st.session_state.forecast_data = result.get("forecast", [])
                st.session_state.alerts_data = result.get("alerts", [])
                st.success("✅ Forecast and Alerts Received!")
            else:
                st.error(f"❌ Backend Error: {response.status_code} - {response.text}")

        except Exception as e:
            st.error(f"⚠️ Error processing CSV: {str(e)}")

# ------------------ Dashboard Page ------------------
def dashboard_page():
    st.title("📊 Inventory Insights Dashboard")
    alerts_data = st.session_state.get('alerts_data')

    if alerts_data:
        for alert in alerts_data:
            st.markdown(f"""
                <h4>🔍 SKU: {alert.get("sku", "N/A")} — {alert.get("product_name", "N/A")}</h4>
                <p><strong>Forecast Window:</strong> {alert.get("forecast_window", "N/A")}</p>
                <p><strong>Avg. Prediction:</strong> {alert.get("avg_prediction", "N/A")} | <strong>Max Predicted Day:</strong> {alert.get("max_predicted_day", "N/A")}</p>
            """, unsafe_allow_html=True)

            for al in alert.get("alerts", []):
                severity_icon = {
                    "High": "🔴",
                    "Medium": "🟠",
                    "Low": "🟢"
                }.get(al.get("severity", "Low"), "⚪")
                st.markdown(f"{severity_icon} **{al.get('type', 'Alert')}** — {al.get('message', '')}")

            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("📥 Please upload a CSV file from the Upload Page to populate this dashboard.")

# ------------------ SKU Comparison Page ------------------
def sku_comparison_page():
    st.title("📈 SKU Forecast Comparison")
    forecast_data = st.session_state.get('forecast_data')

    if forecast_data:
        forecast_df = pd.DataFrame(forecast_data)
        required_cols = {'sku', 'inventory', 'sales', 'date'}

        if required_cols.issubset(forecast_df.columns):
            sku_options = forecast_df["sku"].dropna().unique().tolist()
            selected_sku = st.selectbox("Select an SKU to visualize", sku_options)

            sku_df = forecast_df[forecast_df["sku"] == selected_sku].copy()
            product_name = sku_df["product_name"].dropna().unique()
            st.markdown(f"**Product Name:** {product_name[0] if product_name else 'N/A'}")

            sku_df["date"] = pd.to_datetime(sku_df["date"])
            sku_df.set_index("date", inplace=True)
            st.line_chart(sku_df[["inventory", "sales"]])
        else:
            st.warning("Required columns are missing from the dataset.")
    else:
        st.info("📥 Please upload a CSV file from the Upload Page to visualize SKU comparison.")

# ------------------ Page Controller ------------------
if page == "📤 Upload CSV":
    upload_page()
elif page == "📊 Dashboard":
    dashboard_page()
elif page == "📈 SKU Comparison":
    sku_comparison_page()
