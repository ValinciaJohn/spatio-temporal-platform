# state_store.py — FIXED
#
# Bug fixed: read_state() used `global APP_STATE` and then
# `APP_STATE = json.load(f)` which rebinds the module-level name
# but any other module that already imported APP_STATE directly
# (e.g. `from state_store import APP_STATE`) still holds the old
# dict reference and never sees updates.
#
# Fix: always mutate the SAME dict object in-place using .clear()
# and .update() so all importers see the same live object.
# pipeline.py uses update_state() which calls write_state() → file.
# dashboard.py uses get_state() which calls read_state() → file → dict.
# Both share the same on-disk JSON as the IPC channel.

import json
import threading

STATE_FILE = 'app_state.json'
_lock = threading.Lock()

APP_STATE: dict = {
    'registry':        {},
    'noise_points':    [],
    'cluster_summary': [],
    'anomalies':       [],
    'predictions':     {},
    'drift_events':    [],
    'evolution_log':   [],
    'eval_scores':     {},
    'alerts':          [],
    'total_batches':   0,
    'last_updated':    0.0,
    'throughput':      0.0,
    'map_file':        'live_map.html',
}


def update_state(key: str, value) -> None:
    """Write one key into APP_STATE and flush to disk."""
    APP_STATE[key] = value
    _write_state()


def get_state(key: str):
    """Read from disk into APP_STATE (in-place), then return key."""
    _read_state()
    return APP_STATE.get(key)


def _write_state() -> None:
    """Serialize APP_STATE to JSON, skipping non-serialisable objects."""
    with _lock:
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(APP_STATE, f, default=_safe_serialize)
        except Exception as e:
            print(f'[state_store] write error: {e}')


def _read_state() -> None:
    """
    Read JSON file into APP_STATE IN-PLACE (.clear + .update)
    so all existing references to APP_STATE see the new values.
    """
    global APP_STATE
    try:
        with _lock:
            with open(STATE_FILE, 'r') as f:
                data = json.load(f)
        APP_STATE.clear()
        APP_STATE.update(data)
    except FileNotFoundError:
        pass   # first run before pipeline writes anything
    except Exception as e:
        print(f'[state_store] read error: {e}')


def _safe_serialize(obj):
    """
    JSON fallback serializer — converts objects that json.dump
    can't handle natively (Cluster, TrafficPoint, sets, etc.)
    """
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    if hasattr(obj, '__iter__'):
        return list(obj)
    return str(obj)


# Convenience: expose write for pipeline bootstrap
write_state = _write_state
read_state  = _read_state