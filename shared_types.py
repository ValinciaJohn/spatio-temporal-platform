# shared_types.py  — READ ONLY after Day 1

from dataclasses import dataclass, field
from typing import List, Literal

TrafficRegime = Literal['free_flow','slow','congested','gridlock','unknown']

@dataclass
class TrafficPoint:
    id:          str
    lat:         float
    lon:         float
    timestamp:   float
    speed:       float
    density:     float
    flow:        float
    cluster_id:  int            = -1
    is_anomaly:  bool           = False
    regime:      TrafficRegime  = 'unknown'

@dataclass
class Cluster:
    id:               int
    points:           List[TrafficPoint] = field(default_factory=list)
    centroid_lat:     float = 0.0
    centroid_lon:     float = 0.0
    is_hotspot:       bool  = False
    dominant_regime:  TrafficRegime = 'unknown'
    created_at:       float = 0.0
    updated_at:       float = 0.0