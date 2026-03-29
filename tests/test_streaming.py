# tests/test_streaming.py
# AKILA'S TEST FILE — 12 official pytest tests
# Run: pytest tests/test_streaming.py -v

import pytest
import time
from shared_types import TrafficPoint, Cluster


# ──────────────────────────────────────────────
# TEST 1: row_to_traffic_point
# Verifies CSV row dict becomes TrafficPoint with correct fields
# ──────────────────────────────────────────────
def test_row_to_point():
    from kafka_producer import row_to_traffic_point

    row = {
        'id':        'pt_001',
        'lat':       '39.9042',
        'lon':       '116.4074',
        'timestamp': '1700000000.0',
        'speed':     '45.2',
        'density':   '38.1',
        'flow':      '22.5'
    }
    pt = row_to_traffic_point(row)

    assert pt.id        == 'pt_001'
    assert pt.lat       == 39.9042
    assert pt.lon       == 116.4074
    assert pt.timestamp == 1700000000.0
    assert pt.speed     == 45.2
    assert pt.density   == 38.1
    assert pt.flow      == 22.5
    assert pt.cluster_id  == -1
    assert pt.is_anomaly  == False
    assert pt.regime      == 'unknown'


# ──────────────────────────────────────────────
# TEST 2: point_to_json → json_to_traffic_point round-trip
# Verifies serialization and deserialization return identical object
# ──────────────────────────────────────────────
def test_json_roundtrip():
    from kafka_producer import point_to_json
    from kafka_consumer import json_to_traffic_point

    original = TrafficPoint(
        id='pt_002', lat=39.9042, lon=116.4074,
        timestamp=1700000010.0, speed=42.0,
        density=40.2, flow=21.0,
        cluster_id=-1, is_anomaly=False, regime='unknown'
    )

    json_str     = point_to_json(original)
    reconstructed = json_to_traffic_point(json_str)

    assert reconstructed.id        == original.id
    assert reconstructed.lat       == original.lat
    assert reconstructed.lon       == original.lon
    assert reconstructed.timestamp == original.timestamp
    assert reconstructed.speed     == original.speed
    assert reconstructed.density   == original.density
    assert reconstructed.flow      == original.flow
    assert reconstructed.cluster_id  == original.cluster_id
    assert reconstructed.is_anomaly  == original.is_anomaly
    assert reconstructed.regime      == original.regime


# ──────────────────────────────────────────────
# TEST 3: build_trajectories — 10 sequential points within 30s
# Verifies they are grouped into 1 trajectory
# ──────────────────────────────────────────────
def test_build_trajectories():
    from trajectory_miner import build_trajectories

    pts = [
        TrafficPoint(f'p{i}', 39.92, 116.39,
                     1700000000.0 + i * 3,   # 3s gap — well within 60s
                     45.0, 30.0, 20.0)
        for i in range(10)
    ]
    cluster = Cluster(id=0, points=pts)
    trajs = build_trajectories(cluster)

    assert len(trajs) == 1


# ──────────────────────────────────────────────
# TEST 4: build_trajectories — points with 120s gap
# Verifies they form 2 separate trajectories
# ──────────────────────────────────────────────
def test_trajectory_split_gap():
    from trajectory_miner import build_trajectories

    pts = (
        [TrafficPoint(f'a{i}', 39.92, 116.39,
                      1700000000.0 + i * 5,   # t=0,5,10,15,20
                      45.0, 30.0, 20.0) for i in range(5)] +
        [TrafficPoint(f'b{i}', 39.92, 116.39,
                      1700000000.0 + 200 + i * 5,  # t=200,205... gap=180s
                      45.0, 30.0, 20.0) for i in range(5)]
    )
    cluster = Cluster(id=1, points=pts)
    trajs = build_trajectories(cluster)

    assert len(trajs) == 2


# ──────────────────────────────────────────────
# TEST 5: dtw_distance — series against itself returns 0.0
# ──────────────────────────────────────────────
def test_dtw_self_zero():
    from trajectory_miner import dtw_distance

    s = [10.0, 20.0, 30.0, 40.0, 50.0]
    dist = dtw_distance(s, s)

    assert dist == 0.0


# ──────────────────────────────────────────────
# TEST 6: detect_anomalous_trajectory
# Flat speed series vs spike series flagged as anomaly
# ──────────────────────────────────────────────
def test_anomaly_detected():
    from trajectory_miner import detect_anomalous_trajectory

    # Normal trajectories: flat low speed
    normal_trajs = [
        [TrafficPoint(f'n{j}_p{i}', 39.92, 116.39,
                      1700000000.0 + i * 5, 15.0, 30.0, 20.0)
         for i in range(5)]
        for j in range(3)
    ]

    # Anomalous trajectory: very high speed spike
    anomaly_traj = [
        TrafficPoint(f'a{i}', 39.92, 116.39,
                     1700000000.0 + i * 5, 120.0, 5.0, 40.0)
        for i in range(5)
    ]

    result = detect_anomalous_trajectory(anomaly_traj, normal_trajs, threshold=50.0)

    assert result == True


# ──────────────────────────────────────────────
# TEST 7: classify_regime — gridlock
# speed=5, density=90, flow=5 → 'gridlock'
# ──────────────────────────────────────────────
def test_classify_gridlock():
    from mvts_analyzer import classify_regime

    assert classify_regime(5, 90, 5) == 'gridlock'


# ──────────────────────────────────────────────
# TEST 8: classify_regime — free_flow
# speed=90, density=10, flow=40 → 'free_flow'
# ──────────────────────────────────────────────
def test_classify_free_flow():
    from mvts_analyzer import classify_regime

    assert classify_regime(90, 10, 40) == 'free_flow'


# ──────────────────────────────────────────────
# TEST 9: detect_regime_transitions
# Slow then congested rows → 1 transition in list
# ──────────────────────────────────────────────
def test_transition_detected():
    from mvts_analyzer import extract_time_series, detect_regime_transitions

    pts = [
        TrafficPoint('p1', 39.92, 116.39, 1700000000.0,  50.0, 30.0, 20.0),  # slow
        TrafficPoint('p2', 39.92, 116.39, 1700000010.0,  50.0, 30.0, 20.0),  # slow
        TrafficPoint('p3', 39.92, 116.39, 1700000020.0,  20.0, 60.0, 15.0),  # congested
        TrafficPoint('p4', 39.92, 116.39, 1700000030.0,  20.0, 60.0, 15.0),  # congested
    ]
    cluster = Cluster(id=0, points=pts)
    df = extract_time_series(cluster)
    transitions = detect_regime_transitions(df)

    assert len(transitions) == 1
    assert transitions[0]['from_regime'] == 'slow'
    assert transitions[0]['to_regime']   == 'congested'


# ──────────────────────────────────────────────
# TEST 10: jaccard_similarity — identical snapshots → 1.0
# ──────────────────────────────────────────────
def test_jaccard_identical():
    from drift_detector import jaccard_similarity

    snap = {0: {'size': 5}, 1: {'size': 3}, 2: {'size': 8}}
    assert jaccard_similarity(snap, snap) == 1.0


# ──────────────────────────────────────────────
# TEST 11: jaccard_similarity — disjoint snapshots → 0.0
# ──────────────────────────────────────────────
def test_jaccard_disjoint():
    from drift_detector import jaccard_similarity

    snap1 = {0: {'size': 5}, 1: {'size': 3}}
    snap2 = {2: {'size': 5}, 3: {'size': 3}}
    assert jaccard_similarity(snap1, snap2) == 0.0


def test_drift_triggers():
    from drift_detector import detect_drift

    # Alternating disjoint snapshots → Jaccard = 0.0 every step
    snap_a = {0: {'size': 5}}
    snap_b = {1: {'size': 5}}
    history = [snap_a, snap_b] * 5   # 10 snapshots total

    result = detect_drift(history, window=10, threshold=0.4)

    assert result == True