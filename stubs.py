from shared_types import TrafficPoint, Cluster

# ── VALINCIA'S STUBS (Akila imports these) ─────────────────────────────────

def composite_distance(p1, p2, w_s=0.4, w_t=0.3, w_m=0.3): 
    return 0.5

def run_clustering(points, eps=0.15, min_pts=5): 
    return points, {}

def validate_hotspot(cluster, all_clusters, threshold=3.5): 
    return False

def update_clusters(registry, new_batch, eps=0.15, min_pts=5): 
    return registry

def plot_heatmap(registry, noise_points, filename='live_map.html'): 
    print('[STUB] heatmap')

def get_cluster_summary(registry): 
    return []

# ── AKILA'S STUBS (Valincia imports these) ─────────────────────────────────

def get_next_batch(batch_size=200): 
    return []

def mine_trajectories(cluster):
    return {'frequent_routes':[],'anomalies':[],'trajectory_count':0}

def analyze_mvts(cluster):
    return {'regimes':[],'transitions':[],'prediction':'unknown'}

def detect_drift(history, window=10, threshold=0.4): 
    return False

def handle_drift(registry, recent_points): 
    return registry

def registry_snapshot(registry): 
    return {}