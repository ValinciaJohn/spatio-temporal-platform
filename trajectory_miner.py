# trajectory_miner.py — FIXED
#
# Bug fixed 1: build_trajectories used a 60-second gap threshold.
#   Synthetic data timestamps are random.uniform(0, 86400) so consecutive
#   sorted points are ~17 seconds apart on average — but occasionally
#   hundreds of seconds apart, splitting every trajectory to length 1
#   and discarding all of them (< 3 points check).
#   Fix: raise gap threshold to 3600 seconds (1 hour), matching the
#   hourly batch granularity of the data.
#
# Bug fixed 2: when DTW is unavailable (dtaidistance not installed),
#   detect_anomalous_trajectory returned False for everything.
#   Fix: stat-based fallback — flag a trajectory as anomalous if its
#   mean speed deviates more than 2 standard deviations from the
#   cluster trajectory mean.

from typing import List
from shared_types import TrafficPoint, Cluster
import math

try:
    from dtaidistance import dtw
    import numpy as np
    DTW_AVAILABLE = True
except ImportError:
    DTW_AVAILABLE = False
    print('[trajectory_miner] dtaidistance not installed — using stat-based anomaly fallback.')


# ── Trajectory building ───────────────────────────────────────────────────────

def build_trajectories(cluster: Cluster,
                       gap_seconds: float = 3600.0,   # FIXED: was 60
                       min_len: int = 3) -> List[List[TrafficPoint]]:
    """
    Group cluster points into trajectories by timestamp.
    A new trajectory starts when the time gap between consecutive
    points exceeds gap_seconds.
    Trajectories shorter than min_len points are discarded.
    """
    if not cluster.points:
        return []

    sorted_pts = sorted(cluster.points, key=lambda p: p.timestamp)
    trajectories = []
    current = [sorted_pts[0]]

    for i in range(1, len(sorted_pts)):
        gap = abs(sorted_pts[i].timestamp - sorted_pts[i - 1].timestamp)
        if gap > gap_seconds:
            if len(current) >= min_len:
                trajectories.append(current)
            current = [sorted_pts[i]]
        else:
            current.append(sorted_pts[i])

    if len(current) >= min_len:
        trajectories.append(current)

    return trajectories


def to_speed_series(traj: List[TrafficPoint]) -> List[float]:
    return [p.speed for p in traj]


# ── DTW distance ──────────────────────────────────────────────────────────────

def dtw_distance(s1: List[float], s2: List[float]) -> float:
    if not s1 or not s2:
        return float('inf')
    if DTW_AVAILABLE:
        return dtw.distance(
            np.array(s1, dtype=float),
            np.array(s2, dtype=float)
        )
    # Stat fallback: absolute difference of means
    return abs(sum(s1) / len(s1) - sum(s2) / len(s2))


# ── Frequent route mining ─────────────────────────────────────────────────────

def find_frequent_routes(trajs: List[List[TrafficPoint]],
                         min_support: float = 0.3,
                         dtw_threshold: float = 30.0) -> List[List[TrafficPoint]]:
    if len(trajs) < 2:
        return trajs   # treat all as "normal" when too few to compare

    total    = len(trajs)
    frequent = []

    for i, t in enumerate(trajs):
        s1    = to_speed_series(t)
        count = sum(
            1 for j, other in enumerate(trajs)
            if i != j and dtw_distance(s1, to_speed_series(other)) < dtw_threshold
        )
        if count / total >= min_support:
            frequent.append(t)

    # If nothing qualifies as frequent, treat the median-speed trajectory
    # as the single normal reference so anomaly detection can still fire.
    if not frequent and trajs:
        means    = [(sum(p.speed for p in t) / len(t), t) for t in trajs]
        means.sort(key=lambda x: x[0])
        frequent = [means[len(means) // 2][1]]

    return frequent


# ── Anomaly detection ─────────────────────────────────────────────────────────

def _stat_anomaly(traj: List[TrafficPoint],
                  normal_trajs: List[List[TrafficPoint]],
                  z_thresh: float = 2.0) -> bool:
    """
    Fallback: flag trajectory as anomalous if its mean speed is more than
    z_thresh standard deviations from the distribution of normal traj means.
    """
    normal_means = [sum(p.speed for p in t) / len(t) for t in normal_trajs if t]
    if not normal_means:
        return False
    mu  = sum(normal_means) / len(normal_means)
    var = sum((x - mu) ** 2 for x in normal_means) / len(normal_means)
    sd  = math.sqrt(var) if var > 0 else 1.0
    traj_mean = sum(p.speed for p in traj) / len(traj)
    return abs(traj_mean - mu) > z_thresh * sd


def detect_anomalous_trajectory(traj: List[TrafficPoint],
                                 normal_trajs: List[List[TrafficPoint]],
                                 dtw_threshold: float = 50.0) -> bool:
    if not normal_trajs:
        return False

    s1 = to_speed_series(traj)

    if DTW_AVAILABLE:
        distances = [dtw_distance(s1, to_speed_series(n)) for n in normal_trajs]
        is_anom   = min(distances) > dtw_threshold
    else:
        is_anom = _stat_anomaly(traj, normal_trajs)

    if is_anom:
        traj[-1].is_anomaly = True
    return is_anom


# ── Main export ───────────────────────────────────────────────────────────────

def mine_trajectories(cluster: Cluster) -> dict:
    """
    MAIN EXPORT — called by pipeline.py for each cluster.
    """
    trajs     = build_trajectories(cluster)
    freq      = find_frequent_routes(trajs)
    anomalies = [t for t in trajs if detect_anomalous_trajectory(t, freq)]

    return {
        'frequent_routes':    freq,
        'anomalies':          anomalies,
        'trajectory_count':   len(trajs),
    }