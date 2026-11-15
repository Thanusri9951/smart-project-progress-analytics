import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, IsolationForest

FEATURES=["completion_pct","estimated_hours","actual_hours","delay_days","effort_variance"]

def project_summary(df,risk):
    return {"projects":df.project_id.nunique(),"tasks":len(df),
            "avg_progress":float(df.completion_pct.mean()),
            "delayed":int((df.delay_days>0).sum()),
            "high_risk":int((risk.risk_level=="High").sum())}

def _matrix(df):
    x=df[FEATURES].replace([np.inf,-np.inf],np.nan)
    return SimpleImputer(strategy="median").fit_transform(x)

def make_risk_labels(df):
    out=df.copy()
    def rule(r):
        if r.delay_days>=7 or (r.completion_pct<40 and r.delay_days>0): return "High"
        if r.delay_days>0 or (r.completion_pct<60 and r.status not in ["Not Started","Cancelled"]): return "Medium"
        return "Low"
    out["risk_level"]=out.apply(rule,axis=1)
    out["recommended_action"]=out.risk_level.map({
        "High":"Review blockers, confirm scope and assign support",
        "Medium":"Monitor progress and review workload",
        "Low":"Continue monitoring against the plan"})
    return out

def cluster_tasks(df):
    out=df.copy()
    if len(df)<3:
        out["performance_cluster"]="Insufficient data"
        return out,"At least three rows are required for clustering."
    x=_matrix(df); scaled=StandardScaler().fit_transform(x); k=min(3,len(df))
    model=KMeans(n_clusters=k,random_state=42,n_init=10)
    labels=model.fit_predict(scaled)
    means=pd.DataFrame({"label":labels,"pct":df.completion_pct.values}).groupby("label").pct.mean().sort_values()
    names={}
    labels_order=list(means.index)
    for i,label in enumerate(labels_order):
        names[label]=["Needs attention","Moderate progress","Strong progress"][min(i,2)]
    out["performance_cluster"]=[names[v] for v in labels]
    return out,f"K-Means grouped {len(df)} tasks into {k} clusters using progress, effort and delay indicators. Names are based on average completion."

def train_risk_models(df):
    y=df.risk_level
    if len(df)<12 or y.nunique()<2:
        return {"metrics":[],"importance":pd.DataFrame(columns=["feature","importance"]),"message":"Need at least 12 records and two risk classes."}
    x=_matrix(df)
    strat=y if y.value_counts().min()>=2 else None
    try:
        xtr,xte,ytr,yte=train_test_split(x,y,test_size=.25,random_state=42,stratify=strat)
    except ValueError:
        xtr,xte,ytr,yte=train_test_split(x,y,test_size=.25,random_state=42)
    from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score
    models=[("Decision Tree",DecisionTreeClassifier(max_depth=4,random_state=42,class_weight="balanced")),
            ("Random Forest",RandomForestClassifier(n_estimators=150,max_depth=6,random_state=42,class_weight="balanced"))]
    metrics=[]; fitted=None
    for name,m in models:
        m.fit(xtr,ytr); pred=m.predict(xte)
        metrics.append({"Model":name,"Accuracy":round(accuracy_score(yte,pred),3),
                        "Precision (macro)":round(precision_score(yte,pred,average="macro",zero_division=0),3),
                        "Recall (macro)":round(recall_score(yte,pred,average="macro",zero_division=0),3),
                        "F1 (macro)":round(f1_score(yte,pred,average="macro",zero_division=0),3)})
        if name=="Random Forest": fitted=m
    imp=pd.DataFrame({"feature":FEATURES,"importance":fitted.feature_importances_}).sort_values("importance",ascending=False)
    return {"metrics":metrics,"importance":imp,"message":""}

def detect_anomalies(df):
    out=df.copy()
    if len(df)<8:
        out["anomaly_flag"]="Not evaluated"; return out
    x=_matrix(df)
    model=IsolationForest(contamination="auto",random_state=42)
    pred=model.fit_predict(StandardScaler().fit_transform(x))
    out["anomaly_flag"]=np.where(pred==-1,"Review","Typical")
    return out

def forecast_tasks(df):
    out=df.copy(); today=pd.Timestamp.today().normalize()
    remaining=[]; dates=[]; notes=[]
    for _,r in out.iterrows():
        pct=float(r.completion_pct)
        if pct>=100 or r.status=="Completed":
            remaining.append(0.0); dates.append(r.actual_completion_date if pd.notna(r.actual_completion_date) else today); notes.append("Marked completed")
        elif pd.isna(r.start_date) or pct<=0:
            remaining.append(np.nan); dates.append(pd.NaT); notes.append("Insufficient start date or non-zero progress")
        else:
            elapsed=max(1,(today-r.start_date.normalize()).days)
            rate=pct/elapsed
            days=max(0,(100-pct)/rate)
            remaining.append(round(days,1)); dates.append(today+pd.Timedelta(days=int(np.ceil(days)))); notes.append("Based on average progress per elapsed day")
    out["estimated_remaining_days"]=remaining
    out["estimated_finish_date"]=pd.to_datetime(dates,errors="coerce")
    out["forecast_note"]=notes
    return out

def team_summary(df):
    return df.groupby("team_member",as_index=False).agg(
        task_count=("task_id","count"),average_progress=("completion_pct","mean"),
        average_actual_hours=("actual_hours","mean"),delayed_tasks=("delay_days",lambda s:int((s>0).sum())),
        average_effort_variance=("effort_variance","mean")).sort_values("average_progress",ascending=False)

def association_patterns(df):
    # Simple interpretable co-occurrence rules using discretized attributes; avoids pretending a model has discovered causation.
    if len(df)<10: return pd.DataFrame()
    d=pd.DataFrame(index=df.index)
    d["progress_band"]=pd.cut(df.completion_pct,[-1,39,69,100],labels=["Progress=Low","Progress=Medium","Progress=High"]).astype(str)
    d["delay_band"]=np.where(df.delay_days>0,"Delay=Yes","Delay=No")
    d["effort_band"]=np.where(df.actual_hours>df.estimated_hours*1.2,"Effort=Overrun","Effort=Within")
    d["status_band"]="Status="+df.status.astype(str)
    rows=[]
    for col in d.columns:
        for val,count in d[col].value_counts().items():
            support=count/len(d)
            if support>=.08:
                rows.append({"Pattern":val,"Support":round(support,3),"Interpretation":"Occurs in a notable share of task records"})
    return pd.DataFrame(rows).sort_values("Support",ascending=False).head(15)
