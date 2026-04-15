import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import smtplib
from email.message import EmailMessage

st.set_page_config(page_title="HSE Dashboard", layout="wide")
st.title("🦺 HSE Professional Dashboard")

# =========================
# EMAIL FUNCTION
# =========================
def send_email(pdf_buffer, receiver_email):

    sender_email = st.secrets["EMAIL"]
    app_password = st.secrets["APP_PASSWORD"]

    msg = EmailMessage()
    msg['Subject'] = "HSE KPI Report"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    msg.set_content("Attached is the latest HSE KPI report.")

    msg.add_attachment(
        pdf_buffer.read(),
        maintype='application',
        subtype='pdf',
        filename='HSE_Report.pdf'
    )

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender_email, app_password)
        smtp.send_message(msg)

# =========================
# UPLOAD FILE
# =========================
file = st.file_uploader("Upload HSE KPI File", type=["xlsx"])

if file:

    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()

    # =========================
    # CLEAN DATA
    # =========================
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    numeric_cols = [
        "EPP Total  Worked Man-HRs",
        "Contractor Total  Worked Man-HRs",
        "LWDC", "MTC", "FAC",
        "Near Miss Reports",
        "Number of risk assessment"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = df.dropna(subset=["Date"])

    # =========================
    # KPI CALCULATION
    # =========================
    df["Manhours"] = df["EPP Total  Worked Man-HRs"] + df["Contractor Total  Worked Man-HRs"]

    total_manhours = df["Manhours"].sum()
    total_lti = df["LWDC"].sum()
    total_recordable = df["LWDC"].sum() + df["MTC"].sum() + df["FAC"].sum()

    TRIR = (total_recordable * 200000) / total_manhours if total_manhours else 0
    LTIFR = (total_lti * 1000000) / total_manhours if total_manhours else 0

    # =========================
    # KPIs DISPLAY
    # =========================
    st.subheader("📊 KPIs")

    c1, c2, c3 = st.columns(3)
    c1.metric("TRIR", round(TRIR, 2))
    c2.metric("LTIFR", round(LTIFR, 2))
    c3.metric("Total Recordable", int(total_recordable))

    # =========================
    # TREND
    # =========================
    df["Month"] = df["Date"].dt.to_period("M").astype(str)
    trend = df.groupby("Month").sum(numeric_only=True).reset_index()

    trend["TRIR"] = (trend["LWDC"] + trend["MTC"] + trend["FAC"]) * 200000 / trend["Manhours"]

    st.subheader("📈 Trends")

    st.plotly_chart(px.line(trend, x="Month", y="LWDC", title="LTI Trend"), use_container_width=True)
    st.plotly_chart(px.line(trend, x="Month", y="TRIR", title="TRIR Trend"), use_container_width=True)

    # =========================
    # LEADING INDICATORS
    # =========================
    st.subheader("📊 Leading Indicators")

    if "Near Miss Reports" in trend.columns:
        st.plotly_chart(px.line(trend, x="Month", y="Near Miss Reports", title="Near Miss Trend"), use_container_width=True)

    if "Number of risk assessment" in trend.columns:
        st.plotly_chart(px.line(trend, x="Month", y="Number of risk assessment", title="Risk Assessment Trend"), use_container_width=True)

    # =========================
    # PDF REPORT
    # =========================
   def create_pdf(df, trend, TRIR, LTIFR, total_recordable):

    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from io import BytesIO

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    content = []

    # =========================
    # TITLE
    # =========================
    content.append(Paragraph("HSE KPI REPORT", styles['Title']))
    content.append(Spacer(1, 15))

    # =========================
    # KPI SUMMARY
    # =========================
    content.append(Paragraph("1. KPI Summary", styles['Heading2']))
    content.append(Spacer(1, 10))

    kpi_data = [
        ["Metric", "Value"],
        ["TRIR", round(TRIR, 2)],
        ["LTIFR", round(LTIFR, 2)],
        ["Total Recordable Cases", int(total_recordable)]
    ]

    table = Table(kpi_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))

    content.append(table)
    content.append(Spacer(1, 15))

    # =========================
    # INCIDENT BREAKDOWN
    # =========================
    content.append(Paragraph("2. Incident Breakdown", styles['Heading2']))
    content.append(Spacer(1, 10))

    lti = df["LWDC"].sum()
    mtc = df["MTC"].sum()
    fac = df["FAC"].sum()

    content.append(Paragraph(f"LTI Cases: {lti}", styles['Normal']))
    content.append(Paragraph(f"Medical Cases: {mtc}", styles['Normal']))
    content.append(Paragraph(f"First Aid Cases: {fac}", styles['Normal']))

    content.append(Spacer(1, 15))

    # =========================
    # TREND SUMMARY
    # =========================
    content.append(Paragraph("3. Monthly Trend Summary", styles['Heading2']))
    content.append(Spacer(1, 10))

    last_3 = trend.tail(3)

    for _, row in last_3.iterrows():
        content.append(Paragraph(
            f"{row['Month']}: LTI={int(row['LWDC'])}, TRIR={round(row['TRIR'],2)}",
            styles['Normal']
        ))

    content.append(Spacer(1, 15))

    # =========================
    # LEADING INDICATORS
    # =========================
    content.append(Paragraph("4. Leading Indicators", styles['Heading2']))
    content.append(Spacer(1, 10))

    if "Near Miss Reports" in df.columns:
        content.append(Paragraph(
            f"Total Near Miss Reports: {int(df['Near Miss Reports'].sum())}",
            styles['Normal']
        ))

    if "Number of risk assessment" in df.columns:
        content.append(Paragraph(
            f"Total Risk Assessments: {int(df['Number of risk assessment'].sum())}",
            styles['Normal']
        ))

    content.append(Spacer(1, 15))

    # =========================
    # EXECUTIVE INSIGHT
    # =========================
    content.append(Paragraph("5. Executive Insight", styles['Heading2']))
    content.append(Spacer(1, 10))

    worst_month = trend.loc[trend["LWDC"].idxmax(), "Month"]

    content.append(Paragraph(
        f"Highest incident month: {worst_month}",
        styles['Normal']
    ))

    if TRIR < 1:
        performance = "Excellent"
    elif TRIR < 3:
        performance = "Good"
    else:
        performance = "Needs Improvement"

    content.append(Paragraph(
        f"Overall Safety Performance: {performance}",
        styles['Normal']
    ))

    # =========================
    # BUILD PDF
    # =========================
    doc.build(content)
    buffer.seek(0)

    return buffer

    # =========================
    # DOWNLOAD + EMAIL
    # =========================
    st.subheader("📄 Reporting")

    if st.button("Generate PDF"):
        pdf = create_pdf()
        st.download_button("Download PDF", pdf, "HSE_Report.pdf")

    email_to = st.text_input("📧 Enter email")

    if st.button("Send Email"):
        pdf = create_pdf(df, trend, TRIR, LTIFR, total_recordable)
        send_email(pdf, email_to)
        st.success("✅ Email sent!")
