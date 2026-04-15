import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🦺 HSE Annual KPI Dashboard")

# =========================
# Upload File
# =========================
uploaded_file = st.file_uploader("Upload HSE KPI File", type=["xlsx"])

if uploaded_file:

    # Read file (adjust header if needed)
    df = pd.read_excel(uploaded_file)

    st.subheader("📋 Data Preview")
    st.dataframe(df.head())

    # =========================
    # CLEAN COLUMN NAMES
    # =========================
    df.columns = df.columns.str.strip()

    # =========================
    # COLUMN DETECTION
    # =========================
    cols = df.columns

    # Try to detect important columns
    date_col = [c for c in cols if "month" in c.lower() or "date" in c.lower()]
    manhours_col = [c for c in cols if "man" in c.lower()]
    lti_col = [c for c in cols if "lti" in c.lower()]
    incident_col = [c for c in cols if "incident" in c.lower() or "case" in c.lower()]

    date_col = date_col[0] if date_col else cols[0]
    manhours_col = manhours_col[0] if manhours_col else None
    lti_col = lti_col[0] if lti_col else None
    incident_col = incident_col[0] if incident_col else None

    # =========================
    # KPI CALCULATIONS
    # =========================
    st.subheader("📊 HSE KPIs")

    total_manhours = df[manhours_col].sum() if manhours_col else 0
    total_incidents = df[incident_col].sum() if incident_col else len(df)
    total_lti = df[lti_col].sum() if lti_col else 0

    # TRIR & LTIFR
    TRIR = (total_incidents * 200000) / total_manhours if total_manhours else 0
    LTIFR = (total_lti * 1000000) / total_manhours if total_manhours else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Manhours", int(total_manhours))
    col2.metric("Total Incidents", int(total_incidents))
    col3.metric("LTI", int(total_lti))
    col4.metric("TRIR", round(TRIR, 2))

    st.metric("LTIFR", round(LTIFR, 2))

    # =========================
    # TREND ANALYSIS
    # =========================
    st.subheader("📈 Monthly Trend")

    try:
        fig = px.line(df, x=date_col, y=incident_col, title="Incidents Over Time")
        st.plotly_chart(fig, use_container_width=True)
    except:
        st.warning("Check date or incident column")

    # =========================
    # KPI COMPARISON
    # =========================
    st.subheader("📊 KPI Comparison")

    numeric_cols = df.select_dtypes(include="number").columns

    selected_kpi = st.selectbox("Select KPI", numeric_cols)

    fig2 = px.bar(df, x=date_col, y=selected_kpi, title=f"{selected_kpi} by Month")
    st.plotly_chart(fig2, use_container_width=True)

    # =========================
    # LEADING VS LAGGING
    # =========================
    st.subheader("⚖️ Leading vs Lagging Indicators")

    st.write("Numeric KPIs Overview:")
    st.dataframe(df[numeric_cols].describe())

    # =========================
    # INSIGHTS
    # =========================
    st.subheader("🤖 Insights")

    if incident_col:
        peak_month = df.loc[df[incident_col].idxmax(), date_col]
        st.write(f"🚨 Highest incidents occurred in: **{peak_month}**")

    if lti_col:
        worst_lti = df.loc[df[lti_col].idxmax(), date_col]
        st.write(f"⚠️ Highest LTI month: **{worst_lti}**")
