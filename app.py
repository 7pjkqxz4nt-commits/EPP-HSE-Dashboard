# =========================
# CLEAN DATA (IMPORTANT)
# =========================
df = df[df["Date"].notna()]  # remove empty rows
df = df[df["Date"] != "Annual Planned"]

# Convert date
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

# =========================
# KPI CALCULATIONS
# =========================
st.subheader("📊 Advanced KPIs")

total_manhours = df["EPP Total Worked Man-Hrs"].sum()
safe_manhours = df["EPP Safe worked man-HRs"].sum()

# Example columns (adjust if needed)
lti_col = [c for c in df.columns if "lti" in c.lower()]
incident_col = [c for c in df.columns if "incident" in c.lower()]

lti = df[lti_col[0]].sum() if lti_col else 0
incidents = df[incident_col[0]].sum() if incident_col else len(df)

TRIR = (incidents * 200000) / total_manhours if total_manhours else 0
LTIFR = (lti * 1000000) / total_manhours if total_manhours else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Manhours", int(total_manhours))
col2.metric("Incidents", int(incidents))
col3.metric("TRIR", round(TRIR, 2))
col4.metric("LTIFR", round(LTIFR, 2))

# =========================
# TREND ANALYSIS
# =========================
st.subheader("📈 Trends Over Time")

df["Month"] = df["Date"].dt.to_period("M").astype(str)

trend = df.groupby("Month").sum(numeric_only=True).reset_index()

# Incidents trend
if incident_col:
    fig1 = px.line(trend, x="Month", y=incident_col[0], title="Incident Trend")
    st.plotly_chart(fig1, use_container_width=True)

# Manhours trend
fig2 = px.line(trend, x="Month", y="EPP Total Worked Man-Hrs", title="Manhours Trend")
st.plotly_chart(fig2, use_container_width=True)

# =========================
# ROLLING AVERAGE (VERY IMPORTANT)
# =========================
st.subheader("📉 Rolling Trend (3 Months)")

if incident_col:
    trend["Rolling Avg"] = trend[incident_col[0]].rolling(3).mean()

    fig3 = px.line(
        trend,
        x="Month",
        y=["Rolling Avg"],
        title="3-Month Moving Average"
    )
    st.plotly_chart(fig3, use_container_width=True)

# =========================
# YEARLY COMPARISON
# =========================
st.subheader("📊 Yearly Comparison")

df["Year"] = df["Date"].dt.year

yearly = df.groupby("Year").sum(numeric_only=True).reset_index()

fig4 = px.bar(yearly, x="Year", y="EPP Total Worked Man-Hrs", title="Yearly Manhours")
st.plotly_chart(fig4, use_container_width=True)

# =========================
# INSIGHTS
# =========================
st.subheader("🤖 Insights")

if incident_col:
    worst_month = trend.loc[trend[incident_col[0]].idxmax(), "Month"]
    st.write(f"🚨 Highest incidents occurred in: **{worst_month}**")

best_month = trend.loc[trend["EPP Total Worked Man-Hrs"].idxmax(), "Month"]
st.write(f"🏆 Highest productivity month: **{best_month}**")
