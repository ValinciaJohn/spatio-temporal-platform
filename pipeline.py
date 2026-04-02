# pipeline.py — FINAL
# Order fix: hotspot_validator runs BEFORE analyze_mvts so
# dominant_regime set by validator is not overwritten by MVTS.

from kafka_consumer import get_next_batch
from st_clustering import run_clustering
from hotspot_validator import validate_hotspots
from trajectory_miner import mine_trajectories
from mvts_analyzer import analyze_mvts
from drift_detector import detect_drift, registry_snapshot, handle_drift as _handle_drift
from state_store import update_state, APP_STATE
from cluster_evolution import snapshot_registry as evo_snapshot, update_evolution
from visualizer import plot_heatmap

try:
    from incremental_cluster import update_clusters
except ImportError:
    update_clusters = None

try:
    from evaluation import run_evaluation
    EVAL_OK = True
except ImportError:
    EVAL_OK = False
    print('[PIPELINE] evaluation.py not found — skipping metrics')

try:
    from alert_engine import generate_alerts
    ALERTS_OK = True
except ImportError:
    ALERTS_OK = False
    print('[PIPELINE] alert_engine.py not found — skipping alerts')

import time

snapshot_history = []
evo_history      = []
evolution_log    = []
drift_events     = []   # list of {timestamp, stability, n_clusters}
history          = []
registry         = {}
first_run        = True


def build_cluster_summary(registry, hotspot_results, predictions):
    summary = []
    for cid, cluster in registry.items():
        cid_str   = str(cid)
        hr        = hotspot_results.get(cid, {})
        regime    = getattr(cluster, 'dominant_regime', None) or hr.get('regime', 'unknown')
        is_hot    = getattr(cluster, 'is_hotspot', False)
        predicted = predictions.get(cid_str, predictions.get(cid, '--'))

        summary.append({
            'cluster_id':     cid_str,
            'size':           len(cluster.points),
            'regime':         regime,
            'is_hotspot':     is_hot,
            'predicted':      predicted,
            'centroid_lat':   round(cluster.centroid_lat, 5),
            'centroid_lon':   round(cluster.centroid_lon, 5),
            'avg_speed':      round(hr.get('avg_speed', 0), 2),
            'avg_density':    round(hr.get('avg_density', 0), 2),
            'speed_zscore':   round(hr.get('speed_zscore', 0), 3),
        })

    summary.sort(key=lambda x: x['size'], reverse=True)
    return summary


def main():
    global registry, first_run
    print('[PIPELINE] Starting...')

    while True:
        print('\n[PIPELINE] Reading batch from Kafka...')

        try:
            points = get_next_batch()
        except Exception as e:
            print(f'[PIPELINE] Kafka error: {e}')
            time.sleep(5)
            continue

        if not points:
            print('[PIPELINE] No data received.')
            time.sleep(2)
            continue

        print(f'[PIPELINE] Received {len(points)} points')

        # ── 1. Clustering ──────────────────────────────────────────────────
        if first_run or not update_clusters:
            labeled_points, registry = run_clustering(points)
            first_run = False
        else:
            registry = update_clusters(registry, points)
            labeled_points = [p for c in registry.values() for p in c.points]

        noise_points = [p for p in labeled_points if p.cluster_id == -1]
        total_pts    = len(labeled_points)
        noise_pct    = round(100.0 * len(noise_points) / total_pts, 1) if total_pts else 0.0
        print(f'[PIPELINE] Clusters: {len(registry)} | Noise: {len(noise_points)} ({noise_pct}%)')

        # ── 2. Hotspot validation (MUST run before analyze_mvts) ───────────
        hotspot_results = validate_hotspots(registry)
        hotspot_count   = sum(1 for v in hotspot_results.values() if v.get('is_hotspot'))
        print(f'[PIPELINE] Hotspots: {hotspot_count}')

        # ── 3. Trajectory mining + MVTS prediction ─────────────────────────
        # analyze_mvts runs AFTER hotspot_validator so it won't overwrite
        # the regime that validator correctly set via z-score detection
        all_anomalies = []
        predictions   = {}

        for cid, cluster in registry.items():
            traj_result = mine_trajectories(cluster)
            all_anomalies.extend(traj_result.get('anomalies', []))

            mvts_result      = analyze_mvts(cluster)
            predicted_regime = mvts_result.get('prediction', 'unknown')
            predictions[str(cid)] = predicted_regime
            predictions[cid]      = predicted_regime

        print(f'[PIPELINE] Anomalies: {len(all_anomalies)}')

        # ── 4. Drift detection ─────────────────────────────────────────────
        snap = registry_snapshot(registry)
        snapshot_history.append(snap)
        history.append(snap)

        drift_detected = False
        if len(history) > 2 and detect_drift(history):
            print('[PIPELINE] ⚠ DRIFT DETECTED!')
            drift_detected = True
            drift_events.append({
                'timestamp':  time.time(),
                'n_clusters': len(registry),
                'time_str':   time.strftime('%H:%M:%S'),
            })
            registry = _handle_drift(registry, points)
            history.clear()

        # ── 5. Cluster evolution ───────────────────────────────────────────
        evo_snap_now = evo_snapshot(registry, time.time())
        evo_history.append(evo_snap_now)

        if len(evo_history) >= 2:
            new_log = update_evolution(
                evo_history[-2], evo_history[-1],
                time.time(), list(evolution_log)
            )
            evolution_log.clear()
            evolution_log.extend(new_log)

        if len(evo_history) > 100:
            evo_history.pop(0)

        # ── 6. Evaluation metrics ──────────────────────────────────────────
        eval_scores = {'noise_pct': noise_pct}
        if EVAL_OK:
            eval_scores = run_evaluation(registry, snapshot_history)
            eval_scores['noise_pct'] = noise_pct

        # Compute current stability for dashboard drift panel
        from drift_detector import compute_stability
        stability_now = compute_stability(history) if len(history) >= 2 else 1.0
        eval_scores['stability_now'] = round(stability_now, 4)

        # ── 7. Alerts ──────────────────────────────────────────────────────
        alerts = []
        if ALERTS_OK:
            alerts = generate_alerts(
                registry, all_anomalies,
                [e['timestamp'] for e in drift_events]
            )
            for a in alerts[-3:]:
                print(f'[ALERT] {a}')

        # ── 8. Visualisation ───────────────────────────────────────────────
        plot_heatmap(registry, noise_points, 'live_map.html')

        # ── 9. Write shared state ──────────────────────────────────────────
        cluster_summary = build_cluster_summary(registry, hotspot_results, predictions)

        update_state('cluster_summary', cluster_summary)
        update_state('anomalies',       all_anomalies)
        update_state('predictions',     {str(k): v for k, v in predictions.items()
                                         if isinstance(k, str)})
        update_state('drift_events',    drift_events[-20:])  # last 20 drift events
        update_state('evolution_log',   list(evolution_log))
        update_state('eval_scores',     eval_scores)
        update_state('alerts',          alerts)
        update_state('total_batches',   APP_STATE.get('total_batches', 0) + 1)
        update_state('last_updated',    time.time())
        update_state('map_file',        'live_map.html')

        print(
            f'[PIPELINE] Done — Clusters:{len(registry)} | '
            f'Hotspots:{hotspot_count} | '
            f'Anomalies:{len(all_anomalies)} | '
            f'Alerts:{len(alerts)} | '
            f'Drift events:{len(drift_events)} | '
            f'Evo:{len(evolution_log)}'
        )

        time.sleep(0.5)


if __name__ == '__main__':
    main()