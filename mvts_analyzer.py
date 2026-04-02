# mvts_analyzer.py — FIXED
#
# Bug 1: analyze_mvts() overwrote cluster.dominant_regime with the MVTS
#   regime AFTER hotspot_validator had correctly set it to 'congested'
#   or 'gridlock'. This reset all regime classifications back to free_flow.
#   Fix: only set dominant_regime if hotspot_validator hasn't set a
#   meaningful value yet (i.e. still 'unknown').
#
# Bug 2: classify_regime() thresholds didn't match hotspot_validator.
#   gridlock needed speed<10 AND density>80 AND flow<10 — very strict.
#   With sparse batches, flow is rarely < 10. Now aligned with validator.
#
# Bug 3: predict_next_regime() returned current regime when no transitions
#   observed — fine logically, but meant prediction = current regime always
#   for small clusters. Now falls back to most common regime in history.

from typing import List
import pandas as pd
from shared_types import TrafficPoint, Cluster, TrafficRegime


def classify_regime(speed: float, density: float, flow: float) -> TrafficRegime:
    """
    Classifies a single traffic observation.
    Aligned with hotspot_validator thresholds so regimes are consistent.
    """
    if speed < 8 and density > 60:
        return 'gridlock'
    if speed < 18 and density > 25:
        return 'congested'
    if speed < 35:
        return 'slow'
    return 'free_flow'


def extract_time_series(cluster: Cluster) -> pd.DataFrame:
    if not cluster.points:
        return pd.DataFrame(columns=['timestamp', 'speed', 'density', 'flow', 'regime'])

    sorted_points = sorted(cluster.points, key=lambda p: p.timestamp)

    df = pd.DataFrame([{
        'timestamp': p.timestamp,
        'speed':     p.speed,
        'density':   p.density,
        'flow':      p.flow,
    } for p in sorted_points])

    df['regime'] = df.apply(
        lambda r: classify_regime(r.speed, r.density, r.flow), axis=1
    )
    return df


def detect_regime_transitions(df: pd.DataFrame) -> List[dict]:
    transitions = []
    for i in range(1, len(df)):
        if df['regime'].iloc[i] != df['regime'].iloc[i - 1]:
            transitions.append({
                'from_regime': df['regime'].iloc[i - 1],
                'to_regime':   df['regime'].iloc[i],
                'timestamp':   float(df['timestamp'].iloc[i])
            })
    return transitions


def build_transition_matrix(df: pd.DataFrame) -> dict:
    regimes = ['free_flow', 'slow', 'congested', 'gridlock']
    matrix  = {r: {r2: 0 for r2 in regimes} for r in regimes}
    for i in range(1, len(df)):
        from_r = df['regime'].iloc[i - 1]
        to_r   = df['regime'].iloc[i]
        if from_r in matrix and to_r in matrix[from_r]:
            matrix[from_r][to_r] += 1
    return matrix


def predict_next_regime(df: pd.DataFrame) -> TrafficRegime:
    """
    Predicts next regime via Markov transition matrix.
    If no transitions observed from current regime, returns the most
    common regime in the cluster history (not just current) so the
    prediction is always meaningful.
    """
    if len(df) == 0:
        return 'unknown'

    current = df['regime'].iloc[-1]
    matrix  = build_transition_matrix(df)
    counts  = matrix.get(current, {})

    if all(v == 0 for v in counts.values()):
        # No transitions seen — return most frequent regime overall
        return df['regime'].value_counts().idxmax()

    return max(counts, key=counts.get)


def analyze_mvts(cluster: Cluster) -> dict:
    """
    MAIN EXPORT — called by pipeline.py for each cluster.

    CRITICAL FIX: does NOT overwrite cluster.dominant_regime if
    hotspot_validator has already set it to a meaningful value.
    hotspot_validator runs before analyze_mvts in pipeline.py,
    so its regime classification (z-score based, more accurate for
    sparse batches) takes precedence.
    """
    df = extract_time_series(cluster)

    if len(df) == 0:
        return {'regimes': [], 'transitions': [], 'prediction': 'unknown'}

    transitions = detect_regime_transitions(df)
    prediction  = predict_next_regime(df)

    # Only set dominant_regime if not already set by hotspot_validator
    current_regime = getattr(cluster, 'dominant_regime', 'unknown')
    if not current_regime or current_regime == 'unknown':
        cluster.dominant_regime = df['regime'].value_counts().idxmax()

    return {
        'regimes':     df['regime'].tolist(),
        'transitions': transitions,
        'prediction':  prediction,       # ← this is "next regime"
    }