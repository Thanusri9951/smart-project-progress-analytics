from io import BytesIO
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

def make_text_report(df,risk,forecast,cluster_message):
    lines=["SMART PROJECT PROGRESS ANALYTICS REPORT","",
           f"Projects: {df.project_id.nunique()}",f"Tasks: {len(df)}",
           f"Average task completion: {df.completion_pct.mean():.1f}%",
           f"Delayed tasks: {(df.delay_days>0).sum()}",
           f"High-risk tasks: {(risk.risk_level=='High').sum()}",
           f"Anomaly flags: {int((forecast.get('anomaly_flag',pd.Series(dtype=str))=='Review').sum())}",
           "", "DATA MINING",cluster_message,
           "Risk labels are based on transparent rules. Holdout model metrics show agreement with those rules, not verified future-risk prediction.",
           "", "RECOMMENDATIONS",
           "1. Review high-risk tasks with their owners and record blockers.",
           "2. Validate effort estimates and deadlines.",
           "3. Capture dated progress snapshots regularly for reliable forecasting.",
           "4. Compare model results against actual outcomes before operational use.",
           "", "LIMITATIONS",
           "The dataset may be synthetic or incomplete. Forecasts assume progress remains steady. Anomaly flags are review prompts, not proof of error."]
    return "\n".join(lines)

def make_excel(df,risk,forecast,team):
    bio=BytesIO()
    with pd.ExcelWriter(bio,engine="openpyxl") as w:
        df.to_excel(w,index=False,sheet_name="Tasks")
        risk.to_excel(w,index=False,sheet_name="Risk Analysis")
        forecast.to_excel(w,index=False,sheet_name="Forecast")
        team.to_excel(w,index=False,sheet_name="Team Analytics")
    return bio.getvalue()

def make_pdf(report):
    bio=BytesIO()
    doc=SimpleDocTemplate(bio,pagesize=A4,rightMargin=40,leftMargin=40,topMargin=40,bottomMargin=40)
    styles=getSampleStyleSheet(); story=[]
    for line in report.splitlines():
        story.append(Paragraph(line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;") or "&nbsp;",styles["BodyText"]))
        story.append(Spacer(1,6))
    doc.build(story)
    return bio.getvalue()
