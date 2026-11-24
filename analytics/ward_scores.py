"""Accountability scores per ward: average days to resolve and escalation rate."""
from datetime import datetime

import pandas as pd


def ward_scores(complaints):
    """complaints: list of dicts with ward, status, filed_at, resolved_at."""
    df = pd.DataFrame(complaints)
    if df.empty:
        return []
    df = df[df["filed_at"].notna()].copy()
    if df.empty:
        return []
    filed = pd.to_datetime(df["filed_at"])
    end = pd.to_datetime(df["resolved_at"]).fillna(pd.Timestamp(datetime.now()))
    df["days_open"] = (end - filed).dt.total_seconds() / 86400
    df["escalated"] = df["status"].eq("escalated")
    out = (
        df.groupby("ward")
        .agg(complaints=("status", "size"), avg_days=("days_open", "mean"), escalation_rate=("escalated", "mean"))
        .reset_index()
        .sort_values("avg_days", ascending=False)
    )
    out["avg_days"] = out["avg_days"].round(1)
    out["escalation_rate"] = (out["escalation_rate"] * 100).round(0)
    return out.to_dict(orient="records")
