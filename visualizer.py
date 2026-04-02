# visualizer.py
# Owner: Valincia
# Cleaned: dashboard-friendly map rendering (no UI duplication issues)

import folium
import folium.plugins
from typing import List, Dict
from shared_types import TrafficPoint, Cluster
from config import MAP_OUTPUT_FILE as MAP_FILE


def plot_heatmap(clusters: Dict,
                 noise_points: List[TrafficPoint] = None,
                 filename: str = None) -> str:
    """
    Generate live Folium heatmap.
    - HeatMap layer weighted by inverse speed (slow = hot)
    - Red circles for hotspot clusters
    - Blue circles for normal clusters
    - Grey dots for noise points
    Returns the filename written.
    """

    if filename is None:
        filename = MAP_FILE

    noise_points = noise_points or []

    # Collect all points for centre calculation
    all_pts = [p for cl in clusters.values() for p in cl.points] + noise_points

    if not all_pts:
        m = folium.Map(location=[11.0168, 76.9558], zoom_start=11)
        m.save(filename)
        return filename

    centre_lat = sum(p.lat for p in all_pts) / len(all_pts)
    centre_lon = sum(p.lon for p in all_pts) / len(all_pts)

    # ✅ Clean base map (minimal tiles, looks better in dark UI)
    m = folium.Map(
        location=[centre_lat, centre_lon],
        zoom_start=12,
        control_scale=True
    )

    # ── HeatMap layer ─────────────────────────────────────────────
    heat_data = [
        [p.lat, p.lon, max(1, 120 - p.speed) / 120]
        for cl in clusters.values()
        for p in cl.points
    ]

    if heat_data:
        folium.plugins.HeatMap(
            heat_data,
            radius=15,
            blur=10,
            max_zoom=13
        ).add_to(m)

    # ── Noise points ──────────────────────────────────────────────
    for p in noise_points:
        folium.CircleMarker(
            location=[p.lat, p.lon],
            radius=2,
            color='gray',
            fill=True,
            fill_opacity=0.3
        ).add_to(m)

    # ── Cluster circles ───────────────────────────────────────────
    for cid, cluster in clusters.items():
        if not cluster.points:
            continue

        is_hot = getattr(cluster, 'is_hotspot', False)
        regime = getattr(cluster, 'dominant_regime', 'unknown')

        color = 'red' if is_hot else 'blue'
        fill  = is_hot

        popup_text = (
            f"<b>Cluster {cid}</b><br>"
            f"Size: {len(cluster.points)}<br>"
            f"Regime: {regime}<br>"
            f"Hotspot: {is_hot}"
        )

        folium.Circle(
            location=[cluster.centroid_lat, cluster.centroid_lon],
            radius=300,
            color=color,
            fill=fill,
            fill_opacity=0.3,
            popup=folium.Popup(popup_text, max_width=200)
        ).add_to(m)

    # ✅ Important: save clean HTML (dashboard will embed safely)
    m.save(filename)

    print(f"[MAP] Saved to {filename}")
    return filename


def get_cluster_summary(clusters: Dict) -> List[Dict]:
    """
    MAIN EXPORT for dashboard cluster table.
    Returns list of dicts — one per cluster.
    """

    summary = []

    for cid, cluster in clusters.items():
        summary.append({
            "cluster_id":    cid,
            "size":          len(cluster.points),
            "centroid_lat":  round(cluster.centroid_lat, 5),
            "centroid_lon":  round(cluster.centroid_lon, 5),
            "is_hotspot":    getattr(cluster, 'is_hotspot', False),
            "regime":        getattr(cluster, 'dominant_regime', 'unknown'),
            "updated_at":    getattr(cluster, 'updated_at', 0.0),
        })

    return summary


# ── Backwards-compatible wrapper ────────────────────────────────
def visualize_clusters(points: List[TrafficPoint],
                       output_file: str = "cluster_map.html"):
    """
    Kept for backwards compatibility.
    """

    clusters = {}
    noise = []

    for p in points:
        if p.cluster_id == -1:
            noise.append(p)
        else:
            if p.cluster_id not in clusters:
                c = Cluster(id=p.cluster_id)
                clusters[p.cluster_id] = c
            clusters[p.cluster_id].points.append(p)

    # Compute centroids
    for cid, cl in clusters.items():
        lats = [pt.lat for pt in cl.points]
        lons = [pt.lon for pt in cl.points]
        cl.centroid_lat = sum(lats) / len(lats)
        cl.centroid_lon = sum(lons) / len(lons)

    plot_heatmap(clusters, noise, output_file)