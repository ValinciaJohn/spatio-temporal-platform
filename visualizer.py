# visualizer.py
# Generates a Folium heatmap + cluster markers saved to live_map.html
# Called by pipeline.py: plot_heatmap(registry, noise_points, 'live_map.html')

try:
    import folium
    from folium.plugins import HeatMap
    FOLIUM_OK = True
except ImportError:
    FOLIUM_OK = False
    print('[VISUALIZER] folium not installed — run: pip install folium')

REGIME_COLOURS = {
    'gridlock':  '#ef4444',
    'congested': '#f97316',
    'slow':      '#eab308',
    'free_flow': '#22c55e',
    'unknown':   '#64748b',
}

DEFAULT_LAT = 11.0168
DEFAULT_LON = 76.9558


def _centroid(cluster):
    if hasattr(cluster, 'centroid_lat') and hasattr(cluster, 'centroid_lon'):
        return cluster.centroid_lat, cluster.centroid_lon
    pts = getattr(cluster, 'points', [])
    if not pts:
        return DEFAULT_LAT, DEFAULT_LON
    lats = [getattr(p, 'lat', getattr(p, 'latitude', DEFAULT_LAT)) for p in pts]
    lons = [getattr(p, 'lon', getattr(p, 'longitude', DEFAULT_LON)) for p in pts]
    return sum(lats) / len(lats), sum(lons) / len(lons)


def _point_coords(p):
    lat = getattr(p, 'lat', getattr(p, 'latitude', None))
    lon = getattr(p, 'lon', getattr(p, 'longitude', None))
    return lat, lon


def plot_heatmap(registry: dict, noise_points: list, output_file: str = 'live_map.html'):
    if not FOLIUM_OK:
        _write_placeholder(output_file, "Install folium: pip install folium")
        return

    CBE_BOUNDS = (10.85, 76.75, 11.25, 77.20)

    def _in_cbe(lat, lon):
        return CBE_BOUNDS[0] <= lat <= CBE_BOUNDS[2] and CBE_BOUNDS[1] <= lon <= CBE_BOUNDS[3]

    if registry:
        all_lats, all_lons = [], []
        for cluster in registry.values():
            lat, lon = _centroid(cluster)
            if _in_cbe(lat, lon):
                all_lats.append(lat)
                all_lons.append(lon)
        centre = (sum(all_lats)/len(all_lats), sum(all_lons)/len(all_lons)) if all_lats else (DEFAULT_LAT, DEFAULT_LON)
    else:
        centre = (DEFAULT_LAT, DEFAULT_LON)

    m = folium.Map(
        location=centre,
        zoom_start=13,
        tiles='OpenStreetMap',
        prefer_canvas=True,
    )

    m.fit_bounds([[10.93, 76.88], [11.08, 77.02]])

    heat_data = []
    for cluster in registry.values():
        for p in getattr(cluster, 'points', []):
            lat, lon = _point_coords(p)
            if lat is not None and lon is not None:
                speed  = getattr(p, 'speed', 30)
                weight = max(0.1, 1.0 - min(speed, 80) / 80)
                heat_data.append([lat, lon, weight])

    if heat_data:
        HeatMap(
            heat_data,
            min_opacity=0.3,
            max_zoom=16,
            radius=18,
            blur=15,
            gradient={0.2: '#22c55e', 0.5: '#eab308', 0.75: '#f97316', 1.0: '#ef4444'},
        ).add_to(m)

    for cid, cluster in registry.items():
        lat, lon  = _centroid(cluster)
        regime    = getattr(cluster, 'dominant_regime', 'unknown') or 'unknown'
        is_hot    = getattr(cluster, 'is_hotspot', False)
        size      = len(getattr(cluster, 'points', []))
        colour    = REGIME_COLOURS.get(regime, REGIME_COLOURS['unknown'])

        popup_html = (
            f'<div style="font-family:monospace;font-size:12px;min-width:160px">'
            f'<b style="color:{colour}">Cluster {cid}</b><br>'
            f'Regime: <b>{regime.upper()}</b><br>'
            f'Points: {size}<br>'
            f'Hotspot: {"YES" if is_hot else "No"}<br>'
            f'({lat:.4f}, {lon:.4f})</div>'
        )

        folium.CircleMarker(
            location=(lat, lon),
            radius=10 + min(size / 20, 18),
            color=colour,
            fill=True,
            fill_color=colour,
            fill_opacity=0.55,
            weight=3 if is_hot else 2,
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=f"Cluster {cid} - {regime} - {size} pts",
        ).add_to(m)

        if is_hot:
            folium.CircleMarker(
                location=(lat, lon),
                radius=22,
                color='#ef4444',
                fill=False,
                weight=2,
                opacity=0.6,
                dash_array='6 4',
            ).add_to(m)

    for p in noise_points[::5]:
        lat, lon = _point_coords(p)
        if lat is not None and lon is not None:
            folium.CircleMarker(
                location=(lat, lon),
                radius=2,
                color='#334155',
                fill=True,
                fill_color='#334155',
                fill_opacity=0.5,
                weight=0,
            ).add_to(m)

    try:
        m.save(output_file)
    except Exception as e:
        print(f'[VISUALIZER] Failed to save map: {e}')
        _write_placeholder(output_file, str(e))


def _write_placeholder(output_file: str, msg: str):
    html = (
        '<!DOCTYPE html><html><body style="background:#0a0f1e;color:#64748b;'
        'display:flex;align-items:center;justify-content:center;'
        'height:100vh;font-family:monospace;text-align:center">'
        f'<div><div style="font-size:2rem;margin-bottom:12px">map unavailable</div>'
        f'<small>{msg}</small></div></body></html>'
    )
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)