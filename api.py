from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import json, os, subprocess, threading, collections, sys, re, math

app = FastAPI(title="Traffic Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATE_FILE = "app_state.json"

def read_state():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


# ── Coimbatore Location Lookup ─────────────────────────────────────────────────
# (lat, lon, name) — covers major junctions, roads, areas in Coimbatore
COIMBATORE_LOCATIONS = [
    (11.0168, 76.9558, "Gandhipuram Bus Stand"),
    (11.0183, 76.9725, "RS Puram"),
    (11.0070, 76.9658, "Town Hall Junction"),
    (11.0300, 76.9700, "Peelamedu"),
    (11.0510, 76.9930, "Hopes College"),
    (11.0200, 76.9800, "Tidel Park Junction"),
    (11.0109, 76.9658, "Big Bazaar Street"),
    (11.0250, 76.9600, "Saibaba Colony"),
    (11.0350, 76.9500, "Singanallur"),
    (11.0450, 76.9800, "Avinashi Road"),
    (10.9900, 76.9600, "Ukkadam"),
    (11.0600, 76.9700, "Vadavalli"),
    (11.0150, 77.0100, "Podanur Junction"),
    (11.0550, 77.0300, "Sulur"),
    (10.9800, 77.0000, "Kurichi"),
    (11.0020, 76.9550, "Crosscut Road"),
    (11.0280, 76.9750, "Ramanathapuram"),
    (11.0420, 76.9650, "Kalapatti"),
    (11.0080, 76.9900, "Eachanari"),
    (11.0350, 77.0000, "Saravanampatty"),
    (11.0490, 76.9550, "Kovaipudur"),
    (11.0230, 76.9450, "Krishnarayapuram"),
    (10.9950, 76.9750, "Ganapathy"),
    (11.0130, 76.9820, "Mettupalayam Road"),
    (11.0380, 76.9880, "Kuniyamuthur"),
    (11.0010, 76.9680, "Maruthamalai Road"),
    (11.0620, 76.9900, "Thondamuthur"),
    (11.0290, 76.9330, "Vellalore"),
    (11.0460, 77.0100, "Airport Road"),
    (11.0150, 76.9650, "DB Road"),
]

def _haversine(lat1, lon1, lat2, lon2):
    """Distance in metres between two lat/lon points."""
    R = 6_371_000
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2 +
         math.cos(lat1 * p) * math.cos(lat2 * p) *
         math.sin((lon2 - lon1) * p / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))

def resolve_location(lat, lon, radius_m=800):
    """Return nearest known location name if within radius_m, else coords string."""
    best_dist, best_name = float("inf"), None
    for (plat, plon, pname) in COIMBATORE_LOCATIONS:
        d = _haversine(lat, lon, plat, plon)
        if d < best_dist:
            best_dist, best_name = d, pname
    if best_dist <= radius_m:
        return best_name
    return f"({lat:.4f}, {lon:.4f})"

def _rewrite_alert(alert: str, cluster_map: dict) -> str:
    """Replace 'Cluster N' and raw coords in alert strings with location names."""
    # Replace "Cluster N" with location name if we have centroid data
    def replace_cluster(m):
        cid = int(m.group(1))
        if cid in cluster_map:
            return cluster_map[cid]
        return m.group(0)
    alert = re.sub(r'[Cc]luster\s+(\d+)', replace_cluster, alert)

    def replace_coords(m):
        lat, lon = float(m.group(1)), float(m.group(2))
        return f"near {resolve_location(lat, lon)}"
    alert = re.sub(r'\((\d+\.\d+),\s*(\d+\.\d+)\)', replace_coords, alert)

    return alert

def _build_cluster_map(state: dict) -> dict:
    """Build {cluster_id: location_name} from cluster_summary centroids."""
    cmap = {}
    for c in state.get("cluster_summary", []):
        cid = c.get("cluster_id")
        lat = c.get("centroid_lat")
        lon = c.get("centroid_lon")
        if cid is not None and lat is not None and lon is not None:
            cmap[cid] = resolve_location(lat, lon)
    return cmap


# ── Service Manager ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SERVICE_COMMANDS = {
    "kafka": {
        "cmd": [
            sys.executable,
            os.path.join(BASE_DIR, "kafka_producer.py"),
            "--file", os.path.join(BASE_DIR, "data", "gps_data.csv"),
        ],
        "cwd": BASE_DIR,
    },
    "pipeline": {
        "cmd": [sys.executable, os.path.join(BASE_DIR, "pipeline.py")],
        "cwd": BASE_DIR,
    },

}

_procs: dict[str, subprocess.Popen] = {}
_logs:  dict[str, collections.deque] = {k: collections.deque(maxlen=200) for k in SERVICE_COMMANDS}


def _stream_output(svc_id: str, proc: subprocess.Popen):
    try:
        for raw in proc.stdout:
            line = raw.decode("utf-8", errors="replace").rstrip()
            _logs[svc_id].append(line)
    except Exception:
        pass


def _is_running(svc_id: str) -> bool:
    proc = _procs.get(svc_id)
    return proc is not None and proc.poll() is None


@app.post("/api/services/start/{svc_id}")
def start_service(svc_id: str):
    if svc_id not in SERVICE_COMMANDS:
        return {"ok": False, "error": "Unknown service"}
    if _is_running(svc_id):
        return {"ok": True, "msg": "Already running"}

    cfg = SERVICE_COMMANDS[svc_id]
    _logs[svc_id].clear()
    _logs[svc_id].append(f"[TRAFIX] Starting {svc_id}...")

    try:
        proc = subprocess.Popen(
            cfg["cmd"],
            cwd=cfg["cwd"],
            stdout=subprocess.PIPE,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            stderr=subprocess.STDOUT,
            bufsize=1,
        )
        _procs[svc_id] = proc
        threading.Thread(target=_stream_output, args=(svc_id, proc), daemon=True).start()
        return {"ok": True, "pid": proc.pid}
    except Exception as e:
        _logs[svc_id].append(f"[ERROR] {e}")
        return {"ok": False, "error": str(e)}


@app.post("/api/services/stop/{svc_id}")
def stop_service(svc_id: str):
    if svc_id not in SERVICE_COMMANDS:
        return {"ok": False, "error": "Unknown service"}
    proc = _procs.get(svc_id)
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        _logs[svc_id].append(f"[TRAFIX] {svc_id} stopped.")
    return {"ok": True}


@app.get("/api/services/status")
def get_service_status():
    return {svc: _is_running(svc) for svc in SERVICE_COMMANDS}


@app.get("/api/services/logs/{svc_id}")
def get_service_logs(svc_id: str, lines: int = 40):
    if svc_id not in _logs:
        return {"lines": []}
    return {"lines": list(_logs[svc_id])[-lines:]}


# ── Existing endpoints ─────────────────────────────────────────────────────────

@app.get("/api/summary")
def get_summary():
    state = read_state()
    clusters = state.get("cluster_summary", [])
    # Annotate each cluster with a resolved human-readable location name
    for c in clusters:
        lat = c.get("centroid_lat")
        lon = c.get("centroid_lon")
        if lat is not None and lon is not None:
            c["location_name"] = resolve_location(lat, lon)
        else:
            c["location_name"] = "Unknown"
    return clusters


@app.get("/api/alerts")
def get_alerts():
    state = read_state()
    raw_alerts = state.get("alerts", [])
    cluster_map = _build_cluster_map(state)
    return [_rewrite_alert(a, cluster_map) for a in raw_alerts]


@app.get("/api/evolution")
def get_evolution():
    state = read_state()
    cluster_map = _build_cluster_map(state)
    events = state.get("evolution_log", [])
    for ev in events:
        # dashboard.py reads ev.get('text', ...) — rewrite both fields
        if "text" in ev:
            ev["text"] = _rewrite_alert(ev["text"], cluster_map)
        if "formatted" in ev:
            ev["formatted"] = _rewrite_alert(ev["formatted"], cluster_map)
    return events


@app.get("/api/stats")
def get_stats():
    state = read_state()
    eval_scores   = state.get("eval_scores", {})
    cluster_summ  = state.get("cluster_summary", [])
    anomalies     = state.get("anomalies", [])
    drift_events  = state.get("drift_events", [])

    hotspot_count = sum(1 for c in cluster_summ if c.get("is_hotspot"))

    # stability_now is preferred by the dashboard, falling back to stability
    stability_now = eval_scores.get("stability_now", eval_scores.get("stability", 1.0))

    return {
        # cluster count from cluster_summary (matches dashboard update_stats)
        "clusters":       len(cluster_summ),
        "hotspots":       hotspot_count,
        "anomalies":      len(anomalies),
        "batches":        state.get("total_batches", 0),
        "drift_events":   len(drift_events),
        "silhouette":     round(eval_scores.get("silhouette", 0.0), 3),
        "db_index":       round(eval_scores.get("db_index",   0.0), 3),
        "stability":      round(eval_scores.get("stability",  1.0), 3),
        "stability_now":  round(stability_now, 3),
        "noise_pct":      round(eval_scores.get("noise_pct",  0.0), 1),
        "last_updated":   state.get("last_updated", 0),
        "throughput":     state.get("throughput", 0.0),
    }


@app.get("/api/map", response_class=HTMLResponse)
def get_map():
    map_file = "live_map.html"
    if not os.path.exists(map_file):
        return "<html><body style='background:#0a0f1e;color:#64748b;display:flex;align-items:center;justify-content:center;height:100vh;font-family:monospace'>Waiting for map data...</body></html>"
    with open(map_file, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/drift")
def get_drift():
    state = read_state()
    eval_scores  = state.get("eval_scores", {})
    drift_events = state.get("drift_events", [])

    # Match dashboard logic: prefer stability_now, fall back to stability
    stability = eval_scores.get("stability_now", eval_scores.get("stability", 1.0))

    # Thresholds match dashboard update_drift_panel: >0.7 STABLE, >0.4 UNSTABLE, else DRIFTING
    if stability > 0.7:
        label = "STABLE"
    elif stability > 0.4:
        label = "UNSTABLE"
    else:
        label = "DRIFTING"

    return {
        "stability":    round(stability, 3),
        "label":        label,
        "drift_count":  len(drift_events),
        "drift_events": drift_events[-10:],
    }


@app.get("/api/anomalies")
def get_anomalies():
    """Raw anomaly list — used by dashboard alert feed for colour-coding."""
    state = read_state()
    cluster_map = _build_cluster_map(state)
    anomalies = state.get("anomalies", [])
    # Rewrite location references if anomalies are strings; pass through dicts as-is
    result = []
    for a in anomalies:
        if isinstance(a, str):
            result.append(_rewrite_alert(a, cluster_map))
        else:
            result.append(a)
    return result


@app.get("/api/health")
def health():
    return {"status": "ok", "state_file_exists": os.path.exists(STATE_FILE)}