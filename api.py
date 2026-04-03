# api.py
# FastAPI REST bridge between pipeline state and React frontend
# Place this in your project ROOT (same level as state_store.py)
# Run: uvicorn api:app --host 0.0.0.0 --port 8000 --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import json
import os

app = FastAPI(title="Traffic Intelligence API")

# Allow React dev server (port 3000) and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATE_FILE = "app_state.json"

def read_state():
    """Read shared state from app_state.json written by pipeline.py"""
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


@app.get("/api/summary")
def get_summary():
    """Cluster summary list — used by ClusterTable and RegimeChart"""
    state = read_state()
    return state.get("cluster_summary", [])


@app.get("/api/alerts")
def get_alerts():
    """Latest 20 alerts — used by AlertFeed"""
    state = read_state()
    return state.get("alerts", [])


@app.get("/api/evolution")
def get_evolution():
    """Evolution log — used by EvolutionLog"""
    state = read_state()
    return state.get("evolution_log", [])


@app.get("/api/stats")
def get_stats():
    """Stats bar data — silhouette, stability, noise_pct, batches, etc."""
    state = read_state()
    eval_scores = state.get("eval_scores", {})
    registry    = state.get("registry", {})
    anomalies   = state.get("anomalies", [])
    drift_events = state.get("drift_events", [])

    hotspot_count = 0
    for c in state.get("cluster_summary", []):
        if c.get("is_hotspot"):
            hotspot_count += 1

    return {
        "clusters":      len(registry),
        "hotspots":      hotspot_count,
        "anomalies":     len(anomalies),
        "batches":       state.get("total_batches", 0),
        "drift_events":  len(drift_events),
        "silhouette":    round(eval_scores.get("silhouette", 0.0), 3),
        "stability":     round(eval_scores.get("stability", 1.0), 3),
        "noise_pct":     round(eval_scores.get("noise_pct", 0.0), 1),
        "last_updated":  state.get("last_updated", 0),
        "throughput":    state.get("throughput", 0.0),
    }


@app.get("/api/map", response_class=HTMLResponse)
def get_map():
    """Return live_map.html content as string for iframe srcDoc"""
    map_file = "live_map.html"
    if not os.path.exists(map_file):
        return "<html><body style='background:#0a0f1e;color:#64748b;display:flex;align-items:center;justify-content:center;height:100vh;font-family:monospace'>Waiting for map data...</body></html>"
    with open(map_file, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/drift")
def get_drift():
    """Drift panel data"""
    state = read_state()
    eval_scores  = state.get("eval_scores", {})
    drift_events = state.get("drift_events", [])
    stability    = eval_scores.get("stability", 1.0)

    if stability >= 0.7:
        label = "STABLE"
    elif stability >= 0.55:
        label = "UNSTABLE"
    else:
        label = "DRIFTING"

    return {
        "stability":    round(stability, 3),
        "label":        label,
        "drift_count":  len(drift_events),
        "drift_events": drift_events[-10:],
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "state_file_exists": os.path.exists(STATE_FILE)}