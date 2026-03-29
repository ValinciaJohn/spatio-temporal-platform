from composite_distance import composite_distance


def find_cluster_for_point(point, clusters, eps):
    """
    Assign new point to an existing cluster if within eps distance.
    """

    best_cluster = None
    best_dist = float("inf")

    for cluster_id, cluster_points in clusters.items():

        # compare with cluster centroid (first point approximation)
        representative = cluster_points[0]

        d = composite_distance(point, representative)

        if d < best_dist:
            best_dist = d
            best_cluster = cluster_id

    if best_dist <= eps:
        return best_cluster

    return -1