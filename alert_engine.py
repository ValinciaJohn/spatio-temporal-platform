import time
from typing import Dict, List
from shared_types import Cluster


def _ts() -> str:
    """Current time formatted as HH:MM:SS"""
    return time.strftime("%H:%M:%S")


def congestion_alerts(clusters: Dict) -> List[str]:
    """
    Generate alerts for clusters in congested or gridlock regime.
    Uses cluster.dominant_regime if available, else falls back
    to checking avg speed of points directly.
    """
    alerts = []

    for cid, cluster in clusters.items():
        if not cluster.points:
            continue

        # Get regime — use attribute if set, else compute from avg speed
        regime = getattr(cluster, 'dominant_regime', None)

        if not regime or regime == 'unknown':
            avg_speed = sum(p.speed for p in cluster.points) / len(cluster.points)
            if avg_speed < 10:
                regime = 'gridlock'
            elif avg_speed < 30:
                regime = 'congested'
            else:
                regime = 'ok'

        if regime in ('congested', 'gridlock'):
            size = len(cluster.points)
            if regime == 'gridlock':
                emoji = '🟠'
            elif regime == 'congested':
                emoji = '⚠️'
            else:
                emoji = ''
            alerts.append(
                f"{emoji}  [{_ts()}]  Cluster {cid} is {regime.upper()} "
                f"— {size} vehicles affected"
            )

    return alerts


def hotspot_alerts(clusters: Dict) -> List[str]:
    """
    Generate alerts for clusters flagged as hotspots.
    Reads cluster.is_hotspot attribute.
    """
    alerts = []

    for cid, cluster in clusters.items():
        if getattr(cluster, 'is_hotspot', False):
            lat = round(cluster.centroid_lat, 4)
            lon = round(cluster.centroid_lon, 4)
            alerts.append(
                f"🔴  [{_ts()}]  HOTSPOT confirmed — Cluster {cid} "
                f"at ({lat}, {lon})  |  {len(cluster.points)} points"
            )

    return alerts


def anomaly_alerts(anomalies: List) -> List[str]:
    """
    Generate alerts for route anomalies detected by trajectory_miner.
    anomalies: list of trajectory lists (each trajectory is List[TrafficPoint])
    """
    alerts = []

    for traj in anomalies:
        if not traj:
            continue
        last_pt = traj[-1]
        cid = getattr(last_pt, 'cluster_id', '?')
        alerts.append(
            f"🟡  [{_ts()}]  Route anomaly in Cluster {cid} "
            f"— unusual path detected  |  {len(traj)} points"
        )

    return alerts


def drift_alert(drift_events: List[float]) -> List[str]:
    """
    Generate alert if a drift event occurred recently.
    drift_events: list of Unix timestamps when drift was detected.
    """
    if not drift_events:
        return []

    last = drift_events[-1]
    t = time.strftime("%H:%M:%S", time.localtime(last))
    return [
        f"🔵  [{t}]  DRIFT DETECTED — Traffic pattern changed. "
        f"System re-clustered automatically."
    ]


def generate_alerts(clusters: Dict,
                    anomalies: List,
                    drift_events: List[float]) -> List[str]:
    """
    MAIN EXPORT — called by pipeline.py every batch.

    Combines all alert types sorted by severity:
      🔴 Hotspot  >  ⚠️ Congestion  >  🟡 Anomaly  >  🔵 Drift

    Returns: List[str] — last 20 alerts max
    """
    all_alerts = []

    # Severity order: hotspot first
    all_alerts.extend(hotspot_alerts(clusters))
    all_alerts.extend(congestion_alerts(clusters))
    all_alerts.extend(anomaly_alerts(anomalies))
    all_alerts.extend(drift_alert(drift_events))

    # Return latest 20
    return all_alerts[-20:]



if __name__ == "__main__":
    from shared_types import TrafficPoint, Cluster

    def make_pt(id, speed=5.0):
        p = TrafficPoint(
            id=id, lat=39.9, lon=116.4,
            timestamp=0, speed=speed,
            density=90.0, flow=5.0
        )
        p.cluster_id = 0
        return p

    c0 = Cluster(id=0)
    c0.points = [make_pt(f"p{i}", speed=5.0) for i in range(20)]
    c0.is_hotspot = True
    c0.centroid_lat = 39.9
    c0.centroid_lon = 116.4

    clusters = {0: c0}
    anomalies = [[make_pt("a1"), make_pt("a2")]]
    drift_events = [__import__('time').time()]

    alerts = generate_alerts(clusters, anomalies, drift_events)
    print("[ALERT TEST] Generated alerts:")
    for a in alerts:
        print(" ", a)