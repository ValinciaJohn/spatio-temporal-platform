# evaluation.py
# Owner: Valincia
# Purpose: Compute clustering quality metrics live each batch
# Grounded in: Shekhar et al. 2015 - Section 4.4 (clustering validity)

import numpy as np
from typing import List, Dict
from shared_types import TrafficPoint, Cluster

try:
    from sklearn.metrics import silhouette_score, davies_bouldin_score
    SKLEARN_OK = True
except ImportError:
    SKLEARN_OK = False
    print("[EVAL] sklearn not found. pip install scikit-learn")


def points_to_matrix(points: List[TrafficPoint]) -> np.ndarray:
    """
    Convert TrafficPoints to feature matrix for sklearn metrics.
    6 features: lat, lon, timestamp (normalised), speed, density, flow
    """
    if not points:
        return np.array([])

    return np.array([
        [
            p.lat,
            p.lon,
            p.timestamp / 3600.0,   # normalise hours
            p.speed / 120.0,         # normalise 0-1
            p.density / 150.0,       # normalise 0-1
            p.flow / 60.0            # normalise 0-1
        ]
        for p in points
    ], dtype=np.float32)


def compute_silhouette(points: List[TrafficPoint],
                       labels: List[int]) -> float:
    """
    Silhouette Score: measures how well each point fits its cluster.
    Range: -1 to 1. Higher is better.
    Returns 0.0 if not computable (fewer than 2 clusters).
    """
    if not SKLEARN_OK:
        return 0.0

    unique = set(l for l in labels if l != -1)
    if len(unique) < 2:
        return 0.0

    X = points_to_matrix(points)
    if len(X) < 4:
        return 0.0

    try:
        # Use only non-noise points
        clean_pts = [p for p, l in zip(points, labels) if l != -1]
        clean_labels = [l for l in labels if l != -1]
        if len(set(clean_labels)) < 2:
            return 0.0
        X_clean = points_to_matrix(clean_pts)
        return round(float(silhouette_score(X_clean, clean_labels)), 4)
    except Exception:
        return 0.0


def compute_davies_bouldin(points: List[TrafficPoint],
                           labels: List[int]) -> float:
    """
    Davies-Bouldin Index: ratio of within-cluster scatter to between-cluster separation.
    Range: 0 to inf. Lower is better.
    Returns 99.0 if not computable.
    """
    if not SKLEARN_OK:
        return 99.0

    unique = set(l for l in labels if l != -1)
    if len(unique) < 2:
        return 99.0

    try:
        clean_pts = [p for p, l in zip(points, labels) if l != -1]
        clean_labels = [l for l in labels if l != -1]
        if len(set(clean_labels)) < 2:
            return 99.0
        X_clean = points_to_matrix(clean_pts)
        return round(float(davies_bouldin_score(X_clean, clean_labels)), 4)
    except Exception:
        return 99.0


def compute_noise_ratio(labels: List[int]) -> float:
    """
    Percentage of points labelled as noise (cluster_id == -1).
    Lower is better.
    """
    if not labels:
        return 0.0
    noise = sum(1 for l in labels if l == -1)
    return round(noise / len(labels) * 100, 2)


def compute_temporal_stability(snapshot_history: List[Dict]) -> float:
    """
    Mean Jaccard similarity between consecutive cluster snapshots.
    Measures how stable cluster structure is over time.
    Range: 0 to 1. Higher = more stable.
    Grounded in: Shekhar 2015 Section 4.6 - change footprint patterns
    """
    if len(snapshot_history) < 2:
        return 1.0

    scores = []
    recent = snapshot_history[-10:]  # last 10 snapshots

    for i in range(len(recent) - 1):
        ids1 = set(recent[i].keys())
        ids2 = set(recent[i + 1].keys())

        union = ids1 | ids2
        if not union:
            scores.append(1.0)
            continue

        inter = ids1 & ids2
        scores.append(len(inter) / len(union))

    if not scores:
        return 1.0

    return round(sum(scores) / len(scores), 4)


def run_evaluation(clusters: Dict,
                   snapshot_history: List[Dict]) -> Dict:
    """
    MAIN EXPORT — called by pipeline.py every batch.

    Args:
        clusters:         Dict[int, Cluster] — current cluster registry
        snapshot_history: List[Dict]         — history of registry snapshots

    Returns dict with all four metrics.
    """
    # Collect all points and their labels
    all_points = []
    all_labels = []

    for cid, cluster in clusters.items():
        for p in cluster.points:
            all_points.append(p)
            all_labels.append(cid)

    scores = {
        "silhouette":  compute_silhouette(all_points, all_labels),
        "db_index":    compute_davies_bouldin(all_points, all_labels),
        "noise_pct":   compute_noise_ratio(all_labels),
        "stability":   compute_temporal_stability(snapshot_history),
        "n_clusters":  len(clusters),
        "n_points":    len(all_points),
    }

    return scores


# ── Quick self-test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    from shared_types import TrafficPoint, Cluster
    import time

    def make_pt(id, lat, lon, speed=50.0):
        return TrafficPoint(
            id=id, lat=lat, lon=lon,
            timestamp=time.time(), speed=speed,
            density=30.0, flow=20.0
        )

    # Cluster 0 — tight group near (39.90, 116.40)
    c0 = Cluster(id=0)
    c0.points = [make_pt(f"a{i}", 39.90+i*0.001, 116.40) for i in range(10)]

    # Cluster 1 — tight group near (39.95, 116.45)
    c1 = Cluster(id=1)
    c1.points = [make_pt(f"b{i}", 39.95+i*0.001, 116.45) for i in range(10)]

    clusters = {0: c0, 1: c1}
    history  = [{"0": {}, "1": {}}, {"0": {}, "1": {}}]

    result = run_evaluation(clusters, history)
    print("[EVAL TEST] Results:")
    for k, v in result.items():
        print(f"  {k}: {v}")