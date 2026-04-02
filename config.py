import os

# ── KAFKA ─────────────────────────────────────────────────────────────────
KAFKA_BOOTSTRAP   = os.getenv('KAFKA_BOOTSTRAP', 'localhost:9092')
KAFKA_TOPIC       = os.getenv('KAFKA_TOPIC',     'traffic_stream')
KAFKA_GROUP_ID    = os.getenv('KAFKA_GROUP_ID',  'mobility_pipeline')
# Raised from 500 → 1000 so each batch has more points per cluster
# More points = stabler cluster means = more reliable hotspot/regime detection
KAFKA_BATCH_SIZE  = int(os.getenv('KAFKA_BATCH_SIZE', '1000'))
STREAM_SPEED      = int(os.getenv('STREAM_SPEED', '100'))

# ── CLUSTERING ─────────────────────────────────────────────────────────────
EPS               = float(os.getenv('EPS',        '0.35'))
MIN_PTS           = int(os.getenv('MIN_PTS',      '5'))
W_SPATIAL         = float(os.getenv('W_SPATIAL',  '0.5'))
W_TEMPORAL        = float(os.getenv('W_TEMPORAL', '0.2'))
W_MULTIVAR        = float(os.getenv('W_MULTIVAR', '0.3'))
MAX_DIST_KM       = float(os.getenv('MAX_DIST_KM','2.0'))
MAX_GAP_SEC       = float(os.getenv('MAX_GAP_SEC','86400.0'))
AGE_OUT_SEC       = float(os.getenv('AGE_OUT_SEC','1800.0'))

# ── HOTSPOT ────────────────────────────────────────────────────────────────
HOTSPOT_THRESHOLD = float(os.getenv('HOTSPOT_THRESHOLD','3.5'))
# Lowered from 8 → 3: z-score method works with fewer points
HOTSPOT_MIN_SIZE  = int(os.getenv('HOTSPOT_MIN_SIZE',  '3'))
STUDY_AREA_KM2    = float(os.getenv('STUDY_AREA_KM2', '500.0'))

# ── TRAJECTORY / MVTS ──────────────────────────────────────────────────────
TRAJ_GAP_SEC      = float(os.getenv('TRAJ_GAP_SEC',  '3600.0'))
DTW_THRESHOLD     = float(os.getenv('DTW_THRESHOLD', '50.0'))
MIN_SUPPORT       = float(os.getenv('MIN_SUPPORT',   '0.3'))

# ── DRIFT ──────────────────────────────────────────────────────────────────
DRIFT_WINDOW      = int(os.getenv('DRIFT_WINDOW',     '10'))
DRIFT_THRESHOLD   = float(os.getenv('DRIFT_THRESHOLD','0.4'))

# ── PIPELINE ───────────────────────────────────────────────────────────────
PIPELINE_SLEEP_SEC = int(os.getenv('PIPELINE_SLEEP_SEC','5'))
MAP_OUTPUT_FILE    = os.getenv('MAP_OUTPUT_FILE','live_map.html')

# ── DASHBOARD ──────────────────────────────────────────────────────────────
DASH_PORT         = int(os.getenv('DASH_PORT',      '8050'))
DASH_REFRESH_MS   = int(os.getenv('DASH_REFRESH_MS','5000'))