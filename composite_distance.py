import math
from shared_types import TrafficPoint
from config import MAX_DIST_KM, MAX_GAP_SEC, W_SPATIAL, W_TEMPORAL, W_MULTIVAR

# Computes real-world geographic distance (in km) between two GPS points
def haversine_distance(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

 # Normalizes spatial distance relative to maximum allowed distance
def spatial_component(p1: TrafficPoint, p2: TrafficPoint) -> float:
    dist_km = haversine_distance(p1.lat, p1.lon, p2.lat, p2.lon)
    return min(dist_km / MAX_DIST_KM, 1.0)

# Computes normalized time difference between two points
def temporal_component(p1: TrafficPoint, p2: TrafficPoint) -> float:
    """
    Normalized temporal distance [0, 1].
    FIXED: removed the erroneous * 4 multiplier that capped at MAX_GAP_SEC/4.
    """
    time_gap = abs(p1.timestamp - p2.timestamp)
    return min(time_gap / MAX_GAP_SEC, 1.0)   # was: time_gap / MAX_GAP_SEC * 4

 # Measures similarity in traffic features (speed, density, flow)
def multivariate_component(p1: TrafficPoint, p2: TrafficPoint) -> float:
    def norm_diff(v1, v2):
        denom = max(v1, v2)
        return abs(v1 - v2) / denom if denom > 0 else 0.0

    speed_diff   = norm_diff(p1.speed,   p2.speed)
    density_diff = norm_diff(p1.density, p2.density)
    flow_diff    = norm_diff(p1.flow,    p2.flow)
    return (speed_diff + density_diff + flow_diff) / 3.0

# Combines spatial, temporal, and traffic similarities into one weighted distance
def composite_distance(p1: TrafficPoint, p2: TrafficPoint) -> float:
    spatial  = spatial_component(p1, p2)
    temporal = temporal_component(p1, p2)
    multivar = multivariate_component(p1, p2)
    return W_SPATIAL * spatial + W_TEMPORAL * temporal + W_MULTIVAR * multivar