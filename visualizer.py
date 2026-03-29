import folium
from typing import List
from shared_types import TrafficPoint


def visualize_clusters(points: List[TrafficPoint], output_file="cluster_map.html"):
    """
    Visualize clustered traffic points on a map.
    """

    # Center map roughly around Beijing
    m = folium.Map(location=[39.92, 116.40], zoom_start=11)

    # Simple color palette
    colors = [
        "red", "blue", "green", "purple", "orange",
        "darkred", "cadetblue", "darkgreen", "pink", "black"
    ]

    for p in points:

        # Noise points appear gray
        if p.cluster_id == -1:
            color = "gray"
        else:
            color = colors[p.cluster_id % len(colors)]

        folium.CircleMarker(
            location=[p.lat, p.lon],
            radius=3,
            color=color,
            fill=True,
            fill_opacity=0.7
        ).add_to(m)

    m.save(output_file)

    print(f"[MAP] Saved cluster map to {output_file}")