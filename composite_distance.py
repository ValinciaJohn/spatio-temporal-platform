import math
from shared_types import TrafficPoint
from config import MAX_DIST_KM, MAX_GAP_SEC, W_SPATIAL, W_TEMPORAL, W_MULTIVAR

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Compute Haversine distance between two geographic points in kilometers.
    """

    R = 6371.0  # Earth radius in km

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def spatial_component(p1: TrafficPoint, p2: TrafficPoint):
    """
    Normalized spatial distance between two traffic points.
    """

    dist_km = haversine_distance(
        p1.lat, p1.lon,
        p2.lat, p2.lon
    )

    return min(dist_km / MAX_DIST_KM, 1.0)

def temporal_component(p1: TrafficPoint, p2: TrafficPoint):
    """
    Normalized temporal distance between two traffic points.
    """

    time_gap = abs(p1.timestamp - p2.timestamp)

    return min(time_gap / MAX_GAP_SEC, 1.0)

def multivariate_component(p1: TrafficPoint, p2: TrafficPoint):
    """
    Compare speed, density, and flow differences.
    Returns normalized multivariate distance.
    """

    def norm_diff(v1, v2):
        if max(v1, v2) == 0:
            return 0
        return abs(v1 - v2) / max(v1, v2)

    speed_diff = norm_diff(p1.speed, p2.speed)
    density_diff = norm_diff(p1.density, p2.density)
    flow_diff = norm_diff(p1.flow, p2.flow)

    return (speed_diff + density_diff + flow_diff) / 3.0

def composite_distance(p1: TrafficPoint, p2: TrafficPoint):
    """
    Combined spatio-temporal-multivariate distance.
    """

    spatial = spatial_component(p1, p2)
    temporal = temporal_component(p1, p2)
    multivar = multivariate_component(p1, p2)

    return (
        W_SPATIAL * spatial +
        W_TEMPORAL * temporal +
        W_MULTIVAR * multivar
    )