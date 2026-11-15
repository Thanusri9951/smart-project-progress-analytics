import streamlit as st
import pandas as pd
from src.auth import init_db, login_form, logout, is_admin
from src.data import load_dataset, sample_dataset, validate_dataset, enrich_dataset
from src.analytics import (project_summary, make_risk_labels, cluster_tasks, train_risk_models,
                           detect_anomalies, forecast_tasks, association_patterns, team_summary)
from src.charts import (progress_by_project, status_donut, risk_bar, team_performance,
                        completion_timeline, cluster_scatter, project_comparison_chart)
from src.reports import make_excel, make_pdf, make_text_report
from src.storage import save_upload_log, get_upload_history, add_project_note, get_project_notes

st.set_page_config(page_title="Smart Project Progress Analytics", page_icon="📊", layout="wide")
init_db()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "dataset" not in st.session_state:
    st.session_state.dataset = None
if "dataset_name" not in st.session_state:
    st.session_state.dataset_name = "Sample dataset"

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {background: rgba(120,120,120,.07); padding: 14px; border-radius: 12px;}
div[data-testid="stTabs"] button {font-weight: 600;}
</style>
""", unsafe_allow_html=True)

if not st.session_state.authenticated:
    st.title("📊 Smart Project Progress Analytics")
    st.caption("An intelligent workspace for project monitoring, data mining and decision support.")
    login_form()
    st.stop()

with st.sidebar:
    st.title("📊 Project Analytics")
    st.caption(f"Signed in as **{st.session_state.username}**")
    page = st.radio("Navigation", [
        "Overview Dashboard", "Project Management", "Data Mining Lab",
        "Risk & Anomalies", "Prediction Center", "Team Analytics",
        "Smart Recommendations", "Reports", "Admin Settings"
    ])
    st.divider()
    st.subheader("Dataset")
    uploaded = st.file_uploader("Upload project CSV", type=["csv"], key="dataset_upload")
    if uploaded is not None:
        try:
            raw = pd.read_csv(uploaded)
            clean, warnings = validate_dataset(raw)
            st.session_state.dataset = clean
            st.session_state.dataset_name = uploaded.name
            save_upload_log(uploaded.name, len(clean), st.session_state.username)
            for warning in warnings:
                st.warning(warning)
            st.success(f"Loaded {len(clean)} task records.")
        except Exception as exc:
            st.error(str(exc))
    if st.button("Use built-in sample dataset", use_container_width=True):
        st.session_state.dataset = validate_dataset(sample_dataset())[0]
        st.session_state.dataset_name = "Built-in sample dataset"
        st.rerun()
    st.download_button("Download CSV template", sample_dataset().to_csv(index=False).encode(), "project_data_template.csv", "text/csv", use_container_width=True)
    st.divider()
    st.caption("Academic prototype. Verify model outputs before making project decisions.")
    if st.button("Log out", use_container_width=True):
        logout()
        st.rerun()

if st.session_state.dataset is None:
    st.session_state.dataset = validate_dataset(sample_dataset())[0]
df = enrich_dataset(st.session_state.dataset.copy())
risk_df = make_risk_labels(df)
cluster_df, cluster_message = cluster_tasks(df)
risk_model = train_risk_models(risk_df)
anomaly_df = detect_anomalies(df)
forecast_df = forecast_tasks(df)
summary = project_summary(df, risk_df)
team_df = team_summary(df)

st.title(page)
st.caption(f"Active data: {st.session_state.dataset_name} · {len(df)} task records · {df['project_id'].nunique()} projects")

if page == "Overview Dashboard":
    k = st.columns(5)
    k[0].metric("Projects", summary["projects"])
    k[1].metric("Tasks", summary["tasks"])
    k[2].metric("Average progress", f"{summary['avg_progress']:.1f}%")
    k[3].metric("Delayed tasks", summary["delayed"])
    k[4].metric("High-risk tasks", summary["high_risk"])
    a,b = st.columns(2)
    a.plotly_chart(progress_by_project(df), use_container_width=True)
    b.plotly_chart(status_donut(df), use_container_width=True)
    st.plotly_chart(completion_timeline(df), use_container_width=True)
    st.subheader("Priority tasks")
    st.dataframe(risk_df[risk_df.risk_level.isin(["High","Medium"])][
        ["project_id","task_id","task_name","team_member","completion_pct","delay_days","risk_level","recommended_action"]
    ].sort_values(["risk_level","delay_days"], ascending=[True,False]), use_container_width=True, hide_index=True)

elif page == "Project Management":
    st.subheader("Project and task explorer")
    projects = ["All"] + sorted(df.project_id.astype(str).unique().tolist())
    selected = st.selectbox("Select project", projects)
    view = df if selected == "All" else df[df.project_id.astype(str) == selected]
    st.plotly_chart(progress_by_project(view), use_container_width=True)
    st.dataframe(view.sort_values(["project_id","deadline"]), use_container_width=True, hide_index=True)
    st.subheader("Project notes")
    project_for_note = st.selectbox("Project for note", sorted(df.project_id.astype(str).unique()))
    note = st.text_area("Add a project note or blocker")
    if st.button("Save note"):
        if note.strip():
            add_project_note(project_for_note, note.strip(), st.session_state.username)
            st.success("Note saved.")
    notes = get_project_notes(project_for_note)
    if notes:
        st.dataframe(pd.DataFrame(notes, columns=["Date","Author","Note"]), use_container_width=True, hide_index=True)

elif page == "Data Mining Lab":
    st.subheader("K-Means performance clustering")
    st.info(cluster_message)
    st.plotly_chart(cluster_scatter(cluster_df), use_container_width=True)
    st.dataframe(cluster_df[["project_id","task_id","task_name","completion_pct","actual_hours","delay_days","performance_cluster"]], use_container_width=True, hide_index=True)
    st.divider()
    st.subheader("Risk classification model comparison")
    st.warning("The current risk target is generated from explicit overdue/progress rules. Metrics below measure how well models reproduce those rules on a holdout split, not real-world future risk accuracy. Replace rule labels with verified historical outcomes for genuine prediction.")
    if risk_model["metrics"]:
        st.dataframe(pd.DataFrame(risk_model["metrics"]), use_container_width=True, hide_index=True)
        st.write("Random Forest feature importance")
        st.bar_chart(risk_model["importance"].set_index("feature"))
    else:
        st.info(risk_model["message"])
    st.subheader("Association patterns")
    patterns = association_patterns(df)
    if patterns.empty:
        st.info("Not enough repeated records to form meaningful association patterns.")
    else:
        st.dataframe(patterns, use_container_width=True, hide_index=True)

elif page == "Risk & Anomalies":
    st.subheader("Risk distribution")
    a,b = st.columns(2)
    a.plotly_chart(risk_bar(risk_df), use_container_width=True)
    b.metric("High-risk tasks", int((risk_df.risk_level == "High").sum()))
    st.dataframe(risk_df[["project_id","task_id","task_name","completion_pct","delay_days","risk_level","recommended_action"]], use_container_width=True, hide_index=True)
    st.divider()
    st.subheader("Anomaly detection (Isolation Forest)")
    st.caption("Flags unusual combinations of progress, hours and delay. An anomaly is a review signal, not proof of misconduct or error.")
    st.metric("Flagged unusual tasks", int((anomaly_df.anomaly_flag == "Review").sum()))
    st.dataframe(anomaly_df[["project_id","task_id","task_name","completion_pct","actual_hours","estimated_hours","delay_days","anomaly_flag"]], use_container_width=True, hide_index=True)

elif page == "Prediction Center":
    st.subheader("Task completion estimates")
    st.caption("Estimate based on current completion divided by elapsed calendar days. Requires steady progress and a valid start date; it is not a trained time-series forecast.")
    st.dataframe(forecast_df[["project_id","task_id","task_name","completion_pct","estimated_remaining_days","estimated_finish_date","forecast_note"]], use_container_width=True, hide_index=True)
    valid = forecast_df.estimated_remaining_days.dropna()
    if len(valid):
        st.metric("Median estimated remaining days", f"{valid.median():.1f}")
    st.subheader("Project comparison")
    selected_projects = st.multiselect("Choose projects to compare", sorted(df.project_id.astype(str).unique()), default=sorted(df.project_id.astype(str).unique())[:5])
    compare = df[df.project_id.astype(str).isin(selected_projects)]
    st.plotly_chart(project_comparison_chart(compare), use_container_width=True)

elif page == "Team Analytics":
    st.subheader("Team productivity and workload")
    st.plotly_chart(team_performance(team_df), use_container_width=True)
    st.dataframe(team_df, use_container_width=True, hide_index=True)
    st.caption("Workload is represented by the number of assigned tasks in this dataset. It does not account for task complexity or each person's available capacity.")

elif page == "Smart Recommendations":
    st.subheader("Actionable project insights")
    high = risk_df[risk_df.risk_level == "High"]
    medium = risk_df[risk_df.risk_level == "Medium"]
    if len(high):
        st.error(f"{len(high)} high-risk tasks need immediate review.")
        for _, row in high.head(10).iterrows():
            st.markdown(f"- **{row.task_name} ({row.task_id})**: {row.recommended_action}.")
    if len(medium):
        st.warning(f"{len(medium)} medium-risk tasks should be monitored.")
    if not len(high) and not len(medium):
        st.success("No tasks currently meet the configured medium/high risk rules.")
    slow = team_df.sort_values("average_progress").head(3)
    st.markdown("**Teams/members with lowest average task progress**")
    for _, row in slow.iterrows():
        st.markdown(f"- **{row.team_member}**: {row.average_progress:.1f}% average progress across {row.task_count} tasks. Review assignment context before reallocating work.")
    st.info("Recommendations are generated from transparent rules and summaries. Confirm blockers with task owners before taking action.")

elif page == "Reports":
    st.subheader("Download project reports")
    report = make_text_report(df, risk_df, forecast_df, cluster_message)
    st.download_button("Download text report", report.encode(), "project_analytics_report.txt", "text/plain")
    st.download_button("Download Excel workbook", make_excel(df, risk_df, forecast_df, team_df), "project_analytics_report.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    pdf_bytes = make_pdf(report)
    st.download_button("Download PDF report", pdf_bytes, "project_analytics_report.pdf", "application/pdf")
    st.text_area("Report preview", report, height=300)

elif page == "Admin Settings":
    st.subheader("Administration")
    if not is_admin(st.session_state.username):
        st.warning("This page is restricted to the administrator account.")
    else:
        st.success("Administrator access enabled.")
        st.markdown("**Upload history**")
        history = get_upload_history()
        if history:
            st.dataframe(pd.DataFrame(history, columns=["File","Rows","Uploaded by","Uploaded at"]), use_container_width=True, hide_index=True)
        st.markdown("**Account information**")
        st.write("Default demo admin username: `admin`")
        st.write("Default demo admin password: `Admin@123`")
        st.warning("Change the default password before exposing the application publicly. This prototype stores local SQLite data; cloud deployments may require external persistent storage.")
