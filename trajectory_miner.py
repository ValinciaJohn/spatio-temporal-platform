from typing import List
from shared_types import TrafficPoint, Cluster


try:
    from dtaidistance import dtw
    import numpy as np
    DTW_AVAILABLE = True
except ImportError:
    DTW_AVAILABLE = False
    print('[trajectory_miner] WARNING: dtaidistance not installed. DTW will return inf.')


def build_trajectories(cluster: Cluster) -> List[List[TrafficPoint]]:
    """
    Groups cluster points into individual trajectories.
    Sorts by timestamp, then starts a new trajectory if the
    time gap between consecutive points exceeds 60 seconds.
    Discards trajectories with fewer than 3 points.
    Returns a list of trajectories (each is a List[TrafficPoint]).
    """
    if not cluster.points:
        return []

    sorted_points = sorted(cluster.points, key=lambda p: p.timestamp)

    trajectories = []
    current_traj = [sorted_points[0]]

    for i in range(1, len(sorted_points)):
        p1 = sorted_points[i - 1]
        p2 = sorted_points[i]

        time_gap = abs(p2.timestamp - p1.timestamp)

        if time_gap > 60:
            # Start a new trajectory
            if len(current_traj) >= 3:
                trajectories.append(current_traj)
            current_traj = [p2]
        else:
            current_traj.append(p2)

    # Don't forget the last trajectory
    if len(current_traj) >= 3:
        trajectories.append(current_traj)

    return trajectories


def to_speed_series(traj: List[TrafficPoint]) -> List[float]:
    """
    Extracts the speed values from a trajectory as a plain list of floats.
    Used as input to DTW distance calculation.
    """
    return [p.speed for p in traj]


def dtw_distance(s1: List[float], s2: List[float]) -> float:
    """
    Computes Dynamic Time Warping distance between two speed series.
    Returns float('inf') if either series is empty or dtaidistance
    is not installed.
    """
    if len(s1) == 0 or len(s2) == 0:
        return float('inf')

    if not DTW_AVAILABLE:
        return float('inf')

    return dtw.distance(
        np.array(s1, dtype=float),
        np.array(s2, dtype=float)
    )


def find_frequent_routes(
    trajs: List[List[TrafficPoint]],
    min_support: float = 0.3
) -> List[List[TrafficPoint]]:
    """
    Finds trajectories that are 'similar' to at least min_support
    fraction of all other trajectories, using DTW distance threshold of 30.0.
    Returns the list of frequent trajectories.
    """
    if len(trajs) < 2:
        return []

    frequent = []
    total = len(trajs)

    for i, t in enumerate(trajs):
        s1 = to_speed_series(t)
        count = 0

        for j, other in enumerate(trajs):
            if i == j:
                continue
            s2 = to_speed_series(other)
            if dtw_distance(s1, s2) < 30.0:
                count += 1

        if count / total >= min_support:
            frequent.append(t)

    return frequent


def detect_anomalous_trajectory(
    traj: List[TrafficPoint],
    normal_trajs: List[List[TrafficPoint]],
    threshold: float = 50.0
) -> bool:
    """
    Flags a trajectory as anomalous if its minimum DTW distance
    to all normal (frequent) trajectories exceeds the threshold.
    Sets traj[-1].is_anomaly = True if anomalous.
    Returns True if anomalous, False otherwise.
    """
    if len(normal_trajs) == 0:
        return False

    s1 = to_speed_series(traj)

    distances = [
        dtw_distance(s1, to_speed_series(n))
        for n in normal_trajs
    ]

    min_dist = min(distances)

    if min_dist > threshold:
        traj[-1].is_anomaly = True
        return True

    return False


def mine_trajectories(cluster: Cluster) -> dict:
    """
    MAIN EXPORT — called by pipeline.py for each cluster.
    Builds trajectories, finds frequent routes, detects anomalies.
    Returns a dict with frequent_routes, anomalies, trajectory_count.
    """
    trajs = build_trajectories(cluster)
    freq = find_frequent_routes(trajs)
    anomalies = [t for t in trajs if detect_anomalous_trajectory(t, freq)]

    return {
        'frequent_routes': freq,
        'anomalies': anomalies,
        'trajectory_count': len(trajs)
    }