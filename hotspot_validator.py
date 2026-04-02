# hotspot_validator.py — Z-SCORE EDITION
#
# Root cause of persistent hotspot=0:
#   With KAFKA_BATCH_SIZE=500 and 6000 total data points,
#   each batch gets ~500/6000 = 8% of total points.
#   A hotspot zone with 10% of data → only 4-5 hotspot points per batch.
#   Spread across a cluster of ~100 points = 3-5% hotspot fraction.
#   The old threshold of 25% was NEVER reachable with this batch size.
#
# Fix: Z-SCORE BASED DETECTION
#   Compare each cluster's mean speed and mean density against the
#   distribution of ALL cluster means in this batch.
#   A cluster is a hotspot if its speed z-score < -1.5 AND/OR
#   its density z-score > 1.5 (anomalously slow + dense vs peers).
#   This works even with 3-4 hotspot points because the CLUSTER MEAN
#   is what matters, and 4 points averaging 5 km/h is clearly an
#   outlier vs other clusters averaging 30-40 km/h.
#
# Regime classification uses absolute thresholds on cluster mean
# (not point voting) since means are stable even with sparse data.

import math
from typing import Dict
from shared_types import Cluster

try:
    from config import HOTSPOT_MIN_SIZE
except ImportError:
    HOTSPOT_MIN_SIZE = 3   # lowered: works for sparse batches

# Z-score threshold: cluster must be this many std devs from batch mean
HOTSPOT_SPEED_Z   = -1.5   # anomalously SLOW  (negative = below mean)
HOTSPOT_DENSITY_Z =  1.5   # anomalously DENSE (positive = above mean)


def _mean(values):
    return sum(values) / len(values) if values else 0.0


def _std(values, mean):
    if len(values) < 2:
        return 1.0   # avoid div-by-zero; treat as no deviation
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance) if variance > 0 else 1.0


def compute_cluster_stats(cluster: Cluster):
    n           = len(cluster.points)
    avg_speed   = _mean([p.speed   for p in cluster.points])
    avg_density = _mean([p.density for p in cluster.points])
    avg_flow    = _mean([p.flow    for p in cluster.points])
    return avg_speed, avg_density, avg_flow


def classify_regime_from_mean(avg_speed: float, avg_density: float) -> str:
    """
    Absolute-threshold regime from cluster mean.
    Tuned for Coimbatore zones:
      gridlock  : mean speed < 8  AND density > 60
      congested : mean speed < 18 AND density > 25
      slow      : mean speed < 35
      free_flow : otherwise
    """
    if avg_speed < 8 and avg_density > 60:
        return 'gridlock'
    if avg_speed < 18 and avg_density > 25:
        return 'congested'
    if avg_speed < 35:
        return 'slow'
    return 'free_flow'


def validate_hotspots(clusters: Dict[int, Cluster]) -> Dict[int, dict]:
    """
    MAIN EXPORT — called by pipeline.py every batch.

    Step 1: compute mean speed + density per cluster.
    Step 2: compute z-scores across all clusters in this batch.
    Step 3: flag as hotspot if speed z < HOTSPOT_SPEED_Z
            OR density z > HOTSPOT_DENSITY_Z (and size >= min).
    Step 4: write dominant_regime + is_hotspot back onto each Cluster.
    """

    if not clusters:
        return {}

    # ── Step 1: per-cluster stats ─────────────────────────────────────────
    stats = {}
    for cid, cluster in clusters.items():
        if not cluster.points:
            stats[cid] = (0.0, 0.0, 0.0)
            continue
        stats[cid] = compute_cluster_stats(cluster)

    cluster_ids    = list(clusters.keys())
    speed_means    = [stats[cid][0] for cid in cluster_ids]
    density_means  = [stats[cid][1] for cid in cluster_ids]

    # ── Step 2: batch-level z-score parameters ────────────────────────────
    spd_mean = _mean(speed_means)
    spd_std  = _std(speed_means, spd_mean)
    den_mean = _mean(density_means)
    den_std  = _std(density_means, den_mean)

    # ── Step 3 + 4: classify each cluster ────────────────────────────────
    results = {}
    for cid, cluster in clusters.items():
        avg_speed, avg_density, avg_flow = stats[cid]
        n = len(cluster.points)

        spd_z = (avg_speed   - spd_mean) / spd_std
        den_z = (avg_density - den_mean) / den_std

        # Hotspot if anomalously slow OR anomalously dense vs this batch
        is_hotspot = (
            n >= HOTSPOT_MIN_SIZE and
            (spd_z <= HOTSPOT_SPEED_Z or den_z >= HOTSPOT_DENSITY_Z)
        )

        regime = classify_regime_from_mean(avg_speed, avg_density)

        # ── Write back to cluster object ──────────────────────────────────
        cluster.dominant_regime = regime
        cluster.is_hotspot      = is_hotspot

        results[cid] = {
            'cluster_size': n,
            'avg_speed':    round(avg_speed,   2),
            'avg_density':  round(avg_density, 2),
            'avg_flow':     round(avg_flow,    2),
            'regime':       regime,
            'is_hotspot':   is_hotspot,
            'label':        'congestion' if is_hotspot else regime,
            'speed_zscore': round(spd_z, 3),
            'density_zscore': round(den_z, 3),
        }

    return results