from typing import List
import pandas as pd

from shared_types import TrafficPoint, Cluster, TrafficRegime


def classify_regime(speed: float, density: float, flow: float) -> TrafficRegime:
    """
    Classifies a single traffic observation into a regime.
    Priority order must be followed strictly — gridlock first, free_flow last.

    gridlock:  speed < 10  AND density > 80  AND flow < 10
    congested: speed < 30  AND density > 50
    slow:      speed < 70  AND density > 20
    free_flow: default
    """
    # 1st priority — gridlock
    if speed < 10 and density > 80 and flow < 10:
        return 'gridlock'

    # 2nd priority — congested
    if speed < 30 and density > 50:
        return 'congested'

    # 3rd priority — slow
    if speed < 70 and density > 20:
        return 'slow'

    # 4th priority — default
    return 'free_flow'


def extract_time_series(cluster: Cluster) -> pd.DataFrame:
    """
    Converts cluster points into a time-sorted DataFrame.
    Columns: timestamp, speed, density, flow, regime.
    regime column is computed by applying classify_regime row-wise.
    Returns empty DataFrame if cluster has no points.
    """
    if not cluster.points:
        return pd.DataFrame(columns=['timestamp', 'speed', 'density', 'flow', 'regime'])

    sorted_points = sorted(cluster.points, key=lambda p: p.timestamp)

    df = pd.DataFrame([{
        'timestamp': p.timestamp,
        'speed':     p.speed,
        'density':   p.density,
        'flow':      p.flow
    } for p in sorted_points])

    df['regime'] = df.apply(
        lambda r: classify_regime(r.speed, r.density, r.flow),
        axis=1
    )

    return df


def detect_regime_transitions(df: pd.DataFrame) -> List[dict]:
    """
    Scans the regime column for changes between consecutive rows.
    Returns a list of transition dicts with from_regime, to_regime, timestamp.
    Returns empty list if fewer than 2 rows.
    """
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
    """
    Builds a Markov chain transition count matrix from the regime column.
    matrix[from_regime][to_regime] = number of times that transition occurred.
    All 4 regimes are always present as keys even if count is 0.
    """
    regimes = ['free_flow', 'slow', 'congested', 'gridlock']
    matrix = {r: {r2: 0 for r2 in regimes} for r in regimes}

    for i in range(1, len(df)):
        from_r = df['regime'].iloc[i - 1]
        to_r   = df['regime'].iloc[i]
        if from_r in matrix and to_r in matrix[from_r]:
            matrix[from_r][to_r] += 1

    return matrix


def predict_next_regime(df: pd.DataFrame) -> TrafficRegime:
    """
    Predicts the next traffic regime using the Markov transition matrix.
    Looks at the current (last) regime and returns the most frequent
    next regime seen historically.
    Returns 'unknown' if df is empty.
    Returns current regime if no transitions have been observed from it.
    """
    if len(df) == 0:
        return 'unknown'

    current = df['regime'].iloc[-1]
    matrix = build_transition_matrix(df)
    counts = matrix[current]

    # If no transitions observed from current regime, stay in current
    if all(v == 0 for v in counts.values()):
        return current

    return max(counts, key=counts.get)


def analyze_mvts(cluster: Cluster) -> dict:
    """
    MAIN EXPORT — called by pipeline.py for each cluster.
    Extracts time series, detects transitions, predicts next regime.
    Also sets cluster.dominant_regime to the most common regime.
    Returns dict with regimes list, transitions list, and prediction.
    """
    df = extract_time_series(cluster)

    if len(df) == 0:
        return {
            'regimes':     [],
            'transitions': [],
            'prediction':  'unknown'
        }

    transitions = detect_regime_transitions(df)
    prediction  = predict_next_regime(df)

    # Set dominant regime on the cluster object
    cluster.dominant_regime = df['regime'].value_counts().idxmax()

    return {
        'regimes':     df['regime'].tolist(),
        'transitions': transitions,
        'prediction':  prediction
    }