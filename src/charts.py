import plotly.express as px
import pandas as pd

def progress_by_project(df):
    d=df.groupby(["project_id","project_name"],as_index=False).completion_pct.mean()
    return px.bar(d,x="project_id",y="completion_pct",color="project_name",range_y=[0,100],title="Average task progress by project",labels={"completion_pct":"Average progress (%)"})

def status_donut(df):
    d=df.status.value_counts().rename_axis("Status").reset_index(name="Tasks")
    return px.pie(d,names="Status",values="Tasks",hole=.48,title="Task status distribution")

def risk_bar(df):
    d=df.risk_level.value_counts().rename_axis("Risk").reset_index(name="Tasks")
    return px.bar(d,x="Risk",y="Tasks",color="Risk",title="Project task risk distribution")

def team_performance(d):
    return px.bar(d,x="team_member",y="average_progress",color="task_count",range_y=[0,100],title="Team member average progress",labels={"average_progress":"Average progress (%)","team_member":"Team member"})

def completion_timeline(df):
    d=df.dropna(subset=["start_date"]).groupby("start_date",as_index=False).completion_pct.mean().sort_values("start_date")
    return px.line(d,x="start_date",y="completion_pct",markers=True,title="Average progress by task start date",labels={"completion_pct":"Average progress (%)"})

def cluster_scatter(df):
    return px.scatter(df,x="actual_hours",y="completion_pct",color="performance_cluster",size="estimated_hours",hover_data=["task_id","task_name","project_id"],title="Task performance clusters")

def project_comparison_chart(df):
    d=df.groupby("project_id",as_index=False).agg(progress=("completion_pct","mean"),delay=("delay_days","mean"))
    return px.bar(d,x="project_id",y=["progress","delay"],barmode="group",title="Project progress and average delay",labels={"value":"Value","variable":"Measure"})
