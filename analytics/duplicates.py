"""Group nearby reports of the same issue into one complaint using DBSCAN."""
import numpy as np
from sklearn.cluster import DBSCAN

EARTH_RADIUS_M = 6_371_000


def cluster_reports(reports, radius_m=50, min_samples=1):
    """reports: list of dicts with lat, lon, issue_type.
    Returns a list of cluster labels, one per report.
    Reports of different issue types never share a cluster."""
    labels = [-1] * len(reports)
    next_label = 0
    for issue in {r["issue_type"] for r in reports}:
        idx = [i for i, r in enumerate(reports) if r["issue_type"] == issue]
        coords = np.radians([[reports[i]["lat"], reports[i]["lon"]] for i in idx])
        model = DBSCAN(eps=radius_m / EARTH_RADIUS_M, min_samples=min_samples, metric="haversine")
        for i, lab in zip(idx, model.fit_predict(coords)):
            if lab >= 0:
                labels[i] = next_label + lab
        next_label = max(labels) + 1
    return labels


def find_nearby_duplicate(new_report, existing, radius_m=50):
    """Return the existing report closest to new_report within radius_m
    with the same issue type, or None."""
    best, best_d = None, radius_m
    lat1, lon1 = np.radians([new_report["lat"], new_report["lon"]])
    for r in existing:
        if r["issue_type"] != new_report["issue_type"]:
            continue
        lat2, lon2 = np.radians([r["lat"], r["lon"]])
        a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
        d = 2 * EARTH_RADIUS_M * np.arcsin(np.sqrt(a))
        if d <= best_d:
            best, best_d = r, d
    return best
