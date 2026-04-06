#comparison of cluster centroids

import math
import time
from typing import List

# A cluster centroid must move less than this to be "the same cluster"
# 0.008 degrees ≈ 900m 
DRIFT_DIST_DEG   = 0.008
DRIFT_THRESHOLD  = 0.55   # stability below this → drift
DRIFT_WINDOW     = 8      # compare over last N snapshots


def registry_snapshot(registry: dict) -> dict:
    """
    Snapshot stores centroid as the key signal (not cluster ID).
    Also stores size and regime for diagnostics.
    """
    return {
        cid: {
            'size':         len(c.points),
            'centroid_lat': round(c.centroid_lat, 5),
            'centroid_lon': round(c.centroid_lon, 5),
            'regime':       getattr(c, 'dominant_regime', 'unknown'),
        }
        for cid, c in registry.items()
    }


def _centroid_dist(a: dict, b: dict) -> float:
    dlat = a['centroid_lat'] - b['centroid_lat']
    dlon = a['centroid_lon'] - b['centroid_lon']
    return math.sqrt(dlat**2 + dlon**2)


def _spatial_stability(snap1: dict, snap2: dict) -> float:
    """
    For each cluster in snap2, find nearest cluster in snap1 by centroid.
    Stable if nearest centroid is within DRIFT_DIST_DEG.
    Returns fraction of snap2 clusters that are spatially stable.
    """
    if not snap1 or not snap2:
        return 1.0

    stable = 0
    for cid2, c2 in snap2.items():
        # Find nearest match in snap1
        min_dist = min(
            (_centroid_dist(c2, c1) for c1 in snap1.values()),
            default=float('inf')
        )
        if min_dist <= DRIFT_DIST_DEG:
            stable += 1

    return stable / len(snap2)


def compute_stability(history: List[dict], window: int = DRIFT_WINDOW) -> float:
    """
    Mean spatial stability across last `window` snapshot pairs.
    1.0 = all centroids stable, 0.0 = all centroids shifted.
    """
    recent = history[-window:]
    if len(recent) < 2:
        return 1.0

    scores = [
        _spatial_stability(recent[i], recent[i+1])
        for i in range(len(recent) - 1)
    ]
    return sum(scores) / len(scores)


def detect_drift(history: List[dict],
                 window: int = DRIFT_WINDOW,
                 threshold: float = DRIFT_THRESHOLD) -> bool:
    """
    MAIN EXPORT — returns True if spatial stability drops below threshold.
    Fires when cluster centroids shift significantly between batches,
    indicating a genuine change in traffic distribution.
    """
    stability = compute_stability(history, window)
    if stability < threshold:
        print(f'[DRIFT] Spatial stability={stability:.3f} < {threshold} → DRIFT DETECTED')
        return True
    return False


def handle_drift(registry: dict, recent_points) -> dict:
    """Full re-cluster on drift."""
    print('[DRIFT] Re-clustering from scratch.')
    registry.clear()
    try:
        from st_clustering import run_clustering
    except ImportError:
        from stubs import run_clustering
    _, new_registry = run_clustering(recent_points)
    registry.update(new_registry)
    return registry


# Keep jaccard for backwards compatibility if anything imports it
def jaccard_similarity(snap1: dict, snap2: dict) -> float:
    ids1 = set(snap1.keys())
    ids2 = set(snap2.keys())
    if not (ids1 | ids2):
        return 1.0
    return len(ids1 & ids2) / len(ids1 | ids2)