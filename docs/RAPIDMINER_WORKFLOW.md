# RapidMiner / Altair AI Studio Companion Workflow

The Streamlit application is independently runnable. This document describes a corresponding RapidMiner process for classroom demonstration.

## 1. Read and preprocess
- Read CSV and infer/check attribute types.
- Replace Missing Values for numeric attributes where appropriate.
- Remove Duplicates using task_id.
- Generate Attributes for delay days and effort variance.
- Inspect statistics and distributions.

## 2. K-Means clustering
- Select completion_pct, estimated_hours, actual_hours, delay_days and effort_variance.
- Normalize selected numeric attributes.
- Apply K-Means with k=3.
- Inspect centroids and cluster sizes. Cluster numbers are arbitrary; interpret them from centroid values.

## 3. Risk classification
- Create a transparent risk label using overdue days and completion rules.
- Set the risk field as the label.
- Split data into training and testing sets.
- Train Decision Tree and Random Forest.
- Apply models to test data and evaluate classification performance.
- Explain that rule-derived labels cause models to reproduce the rules; this does not establish real future-risk accuracy.

## 4. Anomaly detection
- Select normalized numerical task indicators.
- Use an available outlier detection operator (for example, Isolation Forest if available in the installed edition).
- Inspect flagged records with task owners. An anomaly is a review signal.

## 5. Forecasting
A simple estimate is:
`remaining_days = (100 - completion_pct) / (completion_pct / elapsed_days)`
It assumes progress remains steady. For genuine forecasting, collect repeated dated snapshots and actual final completion dates.
