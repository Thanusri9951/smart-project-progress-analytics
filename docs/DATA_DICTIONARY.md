# Data Dictionary

| Field | Required | Meaning |
|---|---:|---|
| project_id | Yes | Unique project code |
| project_name | No | Human-readable project name |
| task_id | Yes | Unique task code |
| task_name | Yes | Task description |
| team_member | Yes | Assigned person/team |
| start_date | Yes | Task start date |
| deadline | Yes | Planned deadline |
| actual_completion_date | No | Actual finish date; blank if unfinished |
| estimated_hours | Yes | Planned effort in hours |
| actual_hours | Yes | Recorded effort in hours |
| completion_pct | Yes | Completion from 0 to 100 |
| status | Yes | Completed, In Progress, Not Started, On Hold, Cancelled |

Use YYYY-MM-DD dates, non-negative hours and one row per task. Do not mix hours and days. For better forecasting, keep dated snapshots of completion over time.
