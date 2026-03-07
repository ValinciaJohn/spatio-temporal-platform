from typing import Dict
from shared_types import Cluster

def compute_cluster_stats(cluster: Cluster):
    """
    Compute average traffic metrics for a cluster.
    """

    n = len(cluster.points)

    avg_speed = sum(p.speed for p in cluster.points) / n
    avg_density = sum(p.density for p in cluster.points) / n
    avg_flow = sum(p.flow for p in cluster.points) / n

    return avg_speed, avg_density, avg_flow

def classify_cluster(avg_speed, avg_density):

    # congestion
    if avg_speed < 15 and avg_density > 10:
        return "congestion"

    # slow traffic
    if avg_speed < 40:
        return "slow"

    # free flow
    return "free_flow"

def validate_hotspots(clusters: Dict[int, Cluster]):
    """
    Analyze clusters and assign traffic condition labels.
    """

    results = {}

    for cid, cluster in clusters.items():

        avg_speed, avg_density, avg_flow = compute_cluster_stats(cluster)

        label = classify_cluster(avg_speed, avg_density)

        results[cid] = {
            "cluster_size": len(cluster.points),
            "avg_speed": avg_speed,
            "avg_density": avg_density,
            "avg_flow": avg_flow,
            "label": label
        }

    return results