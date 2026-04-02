# cluster_evolution.py — FIXED
#
# Bug fixed: DBSCAN assigns cluster IDs non-deterministically each batch.
# Cluster "5" in batch N is NOT the same spatial cluster as "5" in batch N+1.
# Old code compared by ID → every cluster looked BORN every single batch,
# SHRINKING/DEAD/GROWING never fired.
#
# Fix: match clusters across snapshots by CENTROID PROXIMITY (nearest
# neighbour within MAX_CENTROID_DIST degrees ~1.1 km). If a previous
# cluster centroid is within that radius, treat it as the same cluster.
# Only then compare sizes for GROWING/STABLE/SHRINKING/DEAD.

import time
import math
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# ~1.1 km in degrees — clusters must move less than this to be "the same"
MAX_CENTROID_DIST = 0.01


@dataclass
class EvolutionEvent:
    cluster_id:   int
    timestamp:    float
    size:         int
    state:        str   # BORN | GROWING | STABLE | SHRINKING | DEAD
    centroid_lat: float
    centroid_lon: float
    regime:       str


# ── Snapshot helper ───────────────────────────────────────────────────────────

def snapshot_registry(registry: dict, timestamp: float) -> Dict[int, dict]:
    """Build a snapshot dict from the live registry."""
    return {
        cid: {
            'size':         len(c.points),
            'centroid_lat': c.centroid_lat,
            'centroid_lon': c.centroid_lon,
            'regime':       getattr(c, 'dominant_regime', 'unknown'),
            'timestamp':    timestamp,
        }
        for cid, c in registry.items()
    }


# ── Centroid matching ─────────────────────────────────────────────────────────

def _centroid_dist(a: dict, b: dict) -> float:
    dlat = a['centroid_lat'] - b['centroid_lat']
    dlon = a['centroid_lon'] - b['centroid_lon']
    return math.sqrt(dlat ** 2 + dlon ** 2)


def _match_clusters(prev_snap: dict,
                    curr_snap: dict) -> Dict[int, Optional[int]]:
    """
    For each current cluster ID, find the best-matching previous cluster
    by centroid proximity.  Returns {curr_id: prev_id | None}.
    """
    matches: Dict[int, Optional[int]] = {}

    for curr_id, curr in curr_snap.items():
        best_prev_id   = None
        best_dist      = MAX_CENTROID_DIST  # threshold

        for prev_id, prev in prev_snap.items():
            d = _centroid_dist(curr, prev)
            if d < best_dist:
                best_dist    = d
                best_prev_id = prev_id

        matches[curr_id] = best_prev_id

    return matches


# ── State classification ──────────────────────────────────────────────────────

def classify_state(curr_size: int, prev_size: Optional[int]) -> str:
    if prev_size is None:
        return 'BORN'
    if curr_size == 0:
        return 'DEAD'
    if curr_size > prev_size * 1.2:
        return 'GROWING'
    if curr_size < prev_size * 0.8:
        return 'SHRINKING'
    return 'STABLE'


# ── Event computation ─────────────────────────────────────────────────────────

def compute_evolution(prev_snap: dict,
                      curr_snap: dict,
                      timestamp: float) -> List[EvolutionEvent]:
    events  = []
    matches = _match_clusters(prev_snap, curr_snap)

    # Current clusters
    for curr_id, curr in curr_snap.items():
        prev_id   = matches.get(curr_id)
        prev_size = prev_snap[prev_id]['size'] if prev_id is not None else None
        state     = classify_state(curr['size'], prev_size)

        events.append(EvolutionEvent(
            cluster_id   = curr_id,
            timestamp    = timestamp,
            size         = curr['size'],
            state        = state,
            centroid_lat = curr['centroid_lat'],
            centroid_lon = curr['centroid_lon'],
            regime       = curr.get('regime', 'unknown'),
        ))

    # Dead clusters — in prev but no curr cluster matched to them
    matched_prev_ids = set(matches.values()) - {None}
    for prev_id, prev in prev_snap.items():
        if prev_id not in matched_prev_ids:
            events.append(EvolutionEvent(
                cluster_id   = prev_id,
                timestamp    = timestamp,
                size         = 0,
                state        = 'DEAD',
                centroid_lat = prev['centroid_lat'],
                centroid_lon = prev['centroid_lon'],
                regime       = prev.get('regime', 'unknown'),
            ))

    return events


# ── Formatting ────────────────────────────────────────────────────────────────

STATE_ICONS = {
    'BORN':      '🟢',
    'GROWING':   '▲',
    'STABLE':    '●',
    'SHRINKING': '▼',
    'DEAD':      '✕',
}

def format_event(event: EvolutionEvent) -> str:
    t    = datetime.fromtimestamp(event.timestamp).strftime('%H:%M:%S')
    icon = STATE_ICONS.get(event.state, '')
    return (
        f'{t}  Cluster {event.cluster_id} {event.state} {icon}'
        f'  {event.size} pts  [{event.regime}]'
    )


# ── Main export ───────────────────────────────────────────────────────────────

def update_evolution(prev_snap: dict,
                     curr_snap: dict,
                     timestamp: float,
                     log: list) -> list:
    """
    MAIN EXPORT — called by pipeline.py every batch.
    prev_snap / curr_snap come from snapshot_history in pipeline.py
    (built by drift_detector.registry_snapshot or our snapshot_registry).
    Returns updated log list capped at 50 entries.
    """
    if not prev_snap or not curr_snap:
        return log

    events = compute_evolution(prev_snap, curr_snap, timestamp)

    for event in events:
        log.append({
            'cluster_id':   event.cluster_id,
            'timestamp':    event.timestamp,
            'size':         event.size,
            'state':        event.state,
            'centroid_lat': event.centroid_lat,
            'centroid_lon': event.centroid_lon,
            'regime':       event.regime,
            'text':         format_event(event),
        })

    return log[-50:]   # cap


# ── Utility ───────────────────────────────────────────────────────────────────

def get_size_history(cluster_id: int, snapshot_history: list) -> List[dict]:
    history = []
    for snap in snapshot_history:
        if cluster_id in snap:
            history.append({
                'timestamp': snap[cluster_id].get('timestamp', 0),
                'size':      snap[cluster_id]['size'],
            })
    return history