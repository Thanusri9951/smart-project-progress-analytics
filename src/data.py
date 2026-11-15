import pandas as pd
import numpy as np

REQUIRED = ["project_id","task_id","task_name","team_member","start_date","deadline",
            "actual_completion_date","estimated_hours","actual_hours","completion_pct","status"]

def sample_dataset():
    rng = np.random.default_rng(27)
    projects = [("PRJ001","E-Commerce Platform"),("PRJ002","Hospital Management"),
                ("PRJ003","Student Portal"),("PRJ004","Inventory System"),
                ("PRJ005","Customer CRM"),("PRJ006","Mobile Banking"),
                ("PRJ007","Library Automation"),("PRJ008","Online Learning"),
                ("PRJ009","Food Delivery"),("PRJ010","HR Portal")]
    tasks = ["Requirements","UI Design","Database Design","Frontend Development","Backend Development",
             "API Integration","Authentication","Testing","Bug Fixing","Documentation",
             "Deployment","Performance Optimization","Security Review","User Acceptance Testing","Maintenance"]
    people = ["Asha","Ravi","Kiran","Meena","Arjun","Priya","Sandeep","Divya","Manoj","Keerthi"]
    rows=[]; n=1; origin=pd.Timestamp("2026-08-01")
    for ix,(pid,pname) in enumerate(projects):
        for j,task in enumerate(tasks):
            start=origin+pd.Timedelta(days=int(rng.integers(ix,45)))
            est=int(rng.integers(8,65)); group=j%5
            pct=int(rng.integers(85,101)) if group==0 else int(rng.integers(50,86)) if group==1 else int(rng.integers(15,56)) if group==2 else int(rng.integers(0,36)) if group==3 else int(rng.integers(65,100))
            actual=round(est*rng.uniform(.7,1.65),1); deadline=start+pd.Timedelta(days=int(rng.integers(5,23)))
            status="Completed" if pct==100 else "Not Started" if pct==0 else "In Progress"
            finish=(deadline+pd.Timedelta(days=int(rng.integers(-2,9)))).strftime("%Y-%m-%d") if status=="Completed" else ""
            rows.append([pid,pname,f"T{n:03d}",task,people[int(rng.integers(10))],start.strftime("%Y-%m-%d"),deadline.strftime("%Y-%m-%d"),finish,est,actual,pct,status]); n+=1
    return pd.DataFrame(rows,columns=["project_id","project_name"]+REQUIRED[1:])

def validate_dataset(raw):
    df=raw.copy()
    df.columns=[str(c).strip().lower().replace(" ","_") for c in df.columns]
    if "project_name" not in df.columns:
        df["project_name"]=df.get("project_id","Project").astype(str)
    missing=[c for c in REQUIRED if c not in df.columns]
    if missing: raise ValueError("Missing required columns: "+", ".join(missing))
    df=df[["project_id","project_name"]+REQUIRED[1:]].copy()
    warnings=[]
    for c in ["project_id","project_name","task_id","task_name","team_member","status"]:
        df[c]=df[c].fillna("Unknown").astype(str).str.strip()
    for c in ["start_date","deadline","actual_completion_date"]:
        df[c]=pd.to_datetime(df[c],errors="coerce")
    for c in ["estimated_hours","actual_hours","completion_pct"]:
        df[c]=pd.to_numeric(df[c],errors="coerce")
    df["estimated_hours"]=df["estimated_hours"].fillna(0).clip(lower=0)
    df["actual_hours"]=df["actual_hours"].fillna(0).clip(lower=0)
    df["completion_pct"]=df["completion_pct"].fillna(0).clip(0,100)
    df["status"]=df["status"].str.title()
    allowed={"Completed","In Progress","Not Started","On Hold","Cancelled"}
    unknown=~df.status.isin(allowed)
    if unknown.any():
        df.loc[unknown,"status"]="In Progress"; warnings.append("Unknown statuses were changed to In Progress.")
    before=len(df); df=df.drop_duplicates("task_id",keep="last")
    if len(df)<before: warnings.append(f"Removed {before-len(df)} duplicate task IDs.")
    if df.empty: raise ValueError("No task records found.")
    return df,warnings

def enrich_dataset(df):
    today=pd.Timestamp.today().normalize()
    df["delay_days"]=0
    active=df.status.ne("Completed") & df.deadline.notna()
    df.loc[active,"delay_days"]=(today-df.loc[active,"deadline"].dt.normalize()).dt.days.clip(lower=0)
    done=df.status.eq("Completed") & df.actual_completion_date.notna() & df.deadline.notna()
    df.loc[done,"delay_days"]=(df.loc[done,"actual_completion_date"].dt.normalize()-df.loc[done,"deadline"].dt.normalize()).dt.days.clip(lower=0)
    df["remaining_pct"]=(100-df.completion_pct).clip(0,100)
    df["effort_variance"]=df.actual_hours-df.estimated_hours
    return df
