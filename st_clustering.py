from typing import List, Dict
from shared_types import TrafficPoint, Cluster
from composite_distance import composite_distance
from config import EPS, MIN_PTS
import time

# Finds neighboring points within eps distance using composite distance (with spatial pruning)
def region_query(points, point, eps):

    neighbors = []

    for p in points:

        # Quick spatial bounding box check (~1 km)
        if abs(point.lat - p.lat) > 0.01 or abs(point.lon - p.lon) > 0.01:
            continue

        if composite_distance(point, p) <= eps:
            neighbors.append(p)

    return neighbors

# Expands a cluster from a core point by iteratively adding density-reachable neighbors
def expand_cluster(points: List[TrafficPoint],
                   point: TrafficPoint,
                   neighbors: List[TrafficPoint],
                   cluster_id: int,
                   eps: float,
                   min_pts: int,
                   visited: set):
    """
    Expand a cluster starting from a core point.
    """

    point.cluster_id = cluster_id
    queue = neighbors.copy()

    while queue:
        current = queue.pop(0)

        if current.id not in visited:
            visited.add(current.id)

            current_neighbors = region_query(points, current, eps)
                
            if len(current_neighbors) >= min_pts:
                for n in current_neighbors:
                    if n.cluster_id == -1:
                        queue.append(n)

        if current.cluster_id == -1:
            current.cluster_id = cluster_id
    
# Main ST-DBSCAN algorithm that assigns cluster IDs and builds cluster structures        
def run_clustering(points: List[TrafficPoint],
                   eps: float = EPS,
                   min_pts: int = MIN_PTS):
    """
    Run ST-DBSCAN clustering using composite distance.
    Returns updated points and a cluster registry.
    """

    visited = set()
    cluster_id = 0

    for p in points:
        p.cluster_id = -1  # initialize as noise

    for point in points:

        if point.id in visited:
            continue

        visited.add(point.id)

        neighbors = region_query(points, point, eps)

        if len(neighbors) < min_pts:
            point.cluster_id = -1
        else:
            expand_cluster(points,
                           point,
                           neighbors,
                           cluster_id,
                           eps,
                           min_pts,
                           visited)

            cluster_id += 1

    # Build cluster registry
    registry: Dict[int, Cluster] = {}

    for p in points:
        if p.cluster_id == -1:
            continue

        if p.cluster_id not in registry:
            registry[p.cluster_id] = Cluster(
                id=p.cluster_id,
                points=[],
                created_at=time.time(),
                updated_at=time.time()
            )

        registry[p.cluster_id].points.append(p)

    # Compute centroids
    for cluster in registry.values():
        lat = sum(p.lat for p in cluster.points) / len(cluster.points)
        lon = sum(p.lon for p in cluster.points) / len(cluster.points)

        cluster.centroid_lat = lat
        cluster.centroid_lon = lon

    return points, registry

