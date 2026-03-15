from typing import List
from shared_types import Cluster


def registry_snapshot(registry: dict) -> dict:
    """
    Creates a lightweight snapshot of the current cluster registry
    for comparison across time steps.
    Each entry captures: size, centroid location, dominant regime.
    """
    return {
        cid: {
            'size':         len(c.points),
            'centroid_lat': c.centroid_lat,
            'centroid_lon': c.centroid_lon,
            'regime':       c.dominant_regime
        }
        for cid, c in registry.items()
    }


def jaccard_similarity(snap1: dict, snap2: dict) -> float:
    """
    Measures structural similarity between two registry snapshots
    using Jaccard similarity on cluster IDs.
    1.0 = identical cluster IDs, 0.0 = no cluster IDs in common.
    Returns 1.0 if both snapshots are empty (no change).
    """
    ids1 = set(snap1.keys())
    ids2 = set(snap2.keys())

    if len(ids1 | ids2) == 0:
        return 1.0

    return len(ids1 & ids2) / len(ids1 | ids2)


def compute_stability(history: List[dict], window: int = 10) -> float:
    """
    Computes mean Jaccard similarity across the last 'window' snapshots.
    High stability (close to 1.0) = cluster structure is consistent.
    Low stability (close to 0.0) = cluster structure is changing rapidly.
    Returns 1.0 if fewer than 2 snapshots available.
    """
    recent = history[-window:]

    if len(recent) < 2:
        return 1.0

    scores = [
        jaccard_similarity(recent[i], recent[i + 1])
        for i in range(len(recent) - 1)
    ]

    return sum(scores) / len(scores)


def detect_drift(history: List[dict], window: int = 10, threshold: float = 0.4) -> bool:
    """
    MAIN EXPORT — called by pipeline.py every cycle.
    Returns True if cluster stability has dropped below threshold,
    indicating a permanent structural change in traffic behaviour.
    """
    stability = compute_stability(history, window)

    if stability < threshold:
        print(f'[DRIFT] Stability={stability:.3f} below threshold={threshold}. Drift detected.')
        return True

    return False


def handle_drift(registry: dict, recent_points) -> dict:
    """
    Responds to detected drift by wiping the existing registry
    and re-clustering from scratch using recent points.
    Uses try/except stub pattern since st_clustering is Valincia's module.
    """
    print('[DRIFT] Full re-clustering triggered.')

    registry.clear()

    try:
        from st_clustering import run_clustering
    except ImportError:
        from stubs import run_clustering

    labeled, new_registry = run_clustering(recent_points)
    registry.update(new_registry)

    return registry