# generate_data.py 

#   Batches 1-50:   morning clusters dominate → certain centroid positions
#   Batches 51-100: evening clusters emerge   → centroids shift → DRIFT
#   Hotspots rotate: A dominates morning, B/C more visible in evening

import random
import csv
import os
import argparse

# Determines realistic base speed for each zone based on peak vs non-peak hours
def get_base_speed(zone_type, hour):
    is_peak = (8 <= hour <= 10) or (17 <= hour <= 20)
    profiles = {
        'city':        (10, 18),
        'market':      (8,  15),
        'it':          (12, 35),
        'residential': (20, 40),
        'outskirts':   (50, 70),
        'hotspot_a':   (3,   6),
        'hotspot_b':   (6,  10),
        'hotspot_c':   (5,   8),
        'anomaly':     (5,  80),
        'shift_early': (8,  12),
        'shift_late':  (6,  10),
    }
    peak_spd, free_spd = profiles.get(zone_type, (30, 50))
    return peak_spd if is_peak else free_spd

# Generates timestamps for each zone to simulate time-based traffic patterns (morning/evening peaks, shifts)
def ts_for_zone(zone_type, start_ts, n):
    if zone_type == 'hotspot_a':
        # Both peaks — present all day
        peaks = [(8*3600, 1.5*3600), (17*3600, 1.5*3600)]
        return [start_ts + max(0, min(86400, random.gauss(*random.choice(peaks))))
                for _ in range(n)]
    elif zone_type == 'hotspot_b':
        # Stronger in morning
        return [start_ts + max(0, min(43200, random.gauss(9*3600, 2*3600)))
                for _ in range(n)]
    elif zone_type == 'hotspot_c':
        # Stronger in evening
        return [start_ts + max(43200, min(86400, random.gauss(18*3600, 2*3600)))
                for _ in range(n)]
    elif zone_type == 'shift_early':
        # ONLY morning 6am-12pm → present in early batches only
        return [start_ts + random.uniform(6*3600, 12*3600) for _ in range(n)]
    elif zone_type == 'shift_late':
        # ONLY evening 4pm-11pm → present in late batches only
        return [start_ts + random.uniform(16*3600, 23*3600) for _ in range(n)]
    else:
        return [start_ts + random.uniform(0, 86400) for _ in range(n)]


# Creates clustered data points with spatial spread and assigns traffic features (speed, density, flow)
def generate_cluster_points(centre_lat, centre_lon, n, zone_type, label,
                             start_ts, spread=0.003):
    results = []
    timestamps = ts_for_zone(zone_type, start_ts, n)

    for i in range(n):
        lat  = centre_lat + random.gauss(0, spread)
        lon  = centre_lon + random.gauss(0, spread)
        ts   = timestamps[i]
        hour = int((ts % 86400) // 3600)
        base = get_base_speed(zone_type, hour)

        if zone_type == 'anomaly':
            # Bimodal: 50% ultra-slow gridlock, 50% sudden fast — maximises z-score
            if random.random() < 0.5:
                speed   = max(0.5, min(4.0,   random.gauss(2, 0.8)))   # near-stopped
                density = max(90.0, min(150.0, random.gauss(120, 8)))   # very dense
            else:
                speed   = max(60.0, min(120.0, random.gauss(90, 12)))   # sudden fast
                density = max(3.0,  min(20.0,  random.gauss(8, 3)))     # nearly empty
        elif zone_type in ('hotspot_a', 'hotspot_b', 'hotspot_c'):
            speed   = max(1.0, min(15.0,  base + random.gauss(0, 1.5)))
            density = max(80.0, min(150.0, 120 + random.gauss(0, 10)))
        elif zone_type in ('shift_early', 'shift_late'):
            speed   = max(1.0, min(20.0,  base + random.gauss(0, 2)))
            density = max(60.0, min(140.0, 100 + random.gauss(0, 8)))
        else:
            speed   = max(1.0,  min(120.0, base + random.gauss(0, 3)))
            density = max(1.0,  min(150.0, 150/max(base,1) + random.gauss(0, 3)))

        # Computes traffic flow using speed-density relationship with added noise for realism
        flow = max(0.1, min(60.0, (speed * density) / 60 + random.gauss(0, 1)))
        results.append({
            'id':        f'{label}_pt_{i:04d}',
            'lat':       str(lat),
            'lon':       str(lon),
            'timestamp': ts,          # keep as float for sorting
            'speed':     str(speed),
            'density':   str(density),
            'flow':      str(flow),
        })
    return results

# Generates random scattered points (noise) to simulate real-world irregular data
def generate_noise_points(n, lat_range, lon_range, start_ts):
    corners = [
        (lat_range[0], lat_range[0]+0.01, lon_range[0], lon_range[0]+0.01),
        (lat_range[1]-0.01, lat_range[1], lon_range[0], lon_range[0]+0.01),
        (lat_range[0], lat_range[0]+0.01, lon_range[1]-0.01, lon_range[1]),
        (lat_range[1]-0.01, lat_range[1], lon_range[1]-0.01, lon_range[1]),
    ]
    results = []
    for i in range(n):
        lat_min, lat_max, lon_min, lon_max = corners[i % 4]
        ts = start_ts + random.uniform(0, 86400)
        results.append({
            'id':        f'noise_pt_{i:04d}',
            'lat':       str(random.uniform(lat_min, lat_max)),
            'lon':       str(random.uniform(lon_min, lon_max)),
            'timestamp': ts,
            'speed':     str(random.uniform(20, 80)),
            'density':   str(random.uniform(5, 40)),
            'flow':      str(random.uniform(5, 30)),
        })
    return results


# Simulates lifecycle of a traffic cluster across phases (born → growing → stable → shrinking → dead)
def generate_evolution_cluster(centre_lat, centre_lon, label, start_ts, phase):
    phase_config = {
        'born':      (50,  15, 60,   0),
        'growing':   (150, 12, 90,   2),
        'stable':    (200, 10, 110,  5),
        'shrinking': (90,  18, 70,   8),
        'dead':      (20,  35, 20,  11),
    }
    n, spd, den, hour_offset = phase_config.get(phase, (50, 20, 50, 0))
    results = []
    for i in range(n):
        lat = centre_lat + random.gauss(0, 0.002)
        lon = centre_lon + random.gauss(0, 0.002)
        ts  = start_ts + hour_offset * 3600 + random.uniform(0, 3600)
        sv  = max(1.0,  min(120.0, spd + random.gauss(0, 2)))
        dv  = max(1.0,  min(150.0, den + random.gauss(0, 5)))
        fv  = max(0.1,  min(60.0, (sv * dv) / 60 + random.gauss(0, 1)))
        results.append({
            'id': f'{label}_{phase}_pt_{i:04d}',
            'lat': str(lat), 'lon': str(lon),
            'timestamp': ts,
            'speed': str(sv), 'density': str(dv), 'flow': str(fv),
        })
    return results

# Sorts all data by timestamp and writes to CSV for chronological streaming
def write_csv(rows, filepath):
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)

    rows.sort(key=lambda r: r['timestamp'])  #ensures time-ordered streaming (drift simulation)
    
    # Convert timestamp to string after sorting
    for r in rows:
        r['timestamp'] = str(r['timestamp'])

    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(
            f, fieldnames=['id', 'lat', 'lon', 'timestamp', 'speed', 'density', 'flow']
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f'[DATA] Written {len(rows)} rows → {filepath}')

# Controls full data generation: zones, hotspots, anomalies, drift, evolution, and noise
def main(n_points=50000, output='data/gps_data.csv'):
    start_ts = 1700000000.0
    random.seed(42)

    centres = [
        # Normal zones
        {'coords': (11.0168, 76.9558), 'type': 'city',        'label': 'gandhipuram'},
        {'coords': (11.0080, 76.9610), 'type': 'city',        'label': 'rs_puram'},
        {'coords': (11.0320, 76.9740), 'type': 'market',      'label': 'singanallur_mkt'},
        {'coords': (10.9980, 76.9560), 'type': 'residential', 'label': 'saibaba_colony'},
        {'coords': (11.0500, 76.9800), 'type': 'it',          'label': 'peelamedu_it'},
        {'coords': (11.0000, 76.9300), 'type': 'outskirts',   'label': 'perur_outskirts'},
        {'coords': (10.9983, 77.0322), 'type': 'residential', 'label': 'hopes_college'},

        # 3 hotspot zones — geographically separated so DBSCAN keeps them distinct
        # A: Town Hall Jn — central, both peaks
        {'coords': (11.0140, 76.9620), 'type': 'hotspot_a', 'label': 'townhall_jn',
         'spread': 0.0008, 'budget_pct': 0.15},
        # B: Ukkadam — southwest, morning dominant (0.55km from A)
        {'coords': (11.0060, 76.9480), 'type': 'hotspot_b', 'label': 'ukkadam_jn',
         'spread': 0.0008, 'budget_pct': 0.10},
        # C: Singanallur — east, evening dominant (1.8km from A)
        {'coords': (11.0100, 76.9950), 'type': 'hotspot_c', 'label': 'singanallur_jn',
         'spread': 0.0008, 'budget_pct': 0.08},

        # Anomaly zone — tight spread so DBSCAN clusters them & trajectory_miner detects
        {'coords': (11.0270, 76.9600), 'type': 'anomaly', 'label': 'airport_approach',
         'spread': 0.0015, 'budget_pct': 0.12},
        # Second anomaly zone — bimodal speed pattern at RS Puram junction
        {'coords': (11.0085, 76.9625), 'type': 'anomaly', 'label': 'rspuram_jn_anomaly',
         'spread': 0.0012, 'budget_pct': 0.08},

        # Shift zones — ONLY in first/second half of day → drift
        {'coords': (11.0400, 76.9450), 'type': 'shift_early', 'label': 'college_morning',
         'spread': 0.002, 'budget_pct': 0.05},
        {'coords': (11.0050, 76.9700), 'type': 'shift_late',  'label': 'mall_evening',
         'spread': 0.002, 'budget_pct': 0.05},
    ]

    all_rows = []
    special_total = sum(int(n_points * c['budget_pct'])
                        for c in centres if 'budget_pct' in c)
    normal_centres = [c for c in centres if 'budget_pct' not in c]
    pts_normal = (n_points - special_total) // len(normal_centres)

    for c in centres:
        n = int(n_points * c['budget_pct']) if 'budget_pct' in c else pts_normal
        all_rows += generate_cluster_points(
            c['coords'][0], c['coords'][1],
            n, c['type'], c['label'], start_ts,
            spread=c.get('spread', 0.003)
        )

    # Evolution cluster
    for phase in ('born', 'growing', 'stable', 'shrinking', 'dead'):
        all_rows += generate_evolution_cluster(
            11.0230, 76.9650, 'ukkadam_evo', start_ts, phase
        )

    # Noise
    all_rows += generate_noise_points(
        int(n_points * 0.04), (10.95, 11.08), (76.90, 77.05), start_ts
    )

    write_csv(all_rows, output)  # sorts by timestamp internally

    total = len(all_rows)
    print(f'\n[SUMMARY]')
    print(f'  Total points   : {total}')
    print(f'  Sorted by      : timestamp (chronological streaming)')
    print(f'  Early batches  : morning traffic + college_morning cluster')
    print(f'  Later batches  : evening traffic + mall_evening cluster')
    print(f'  Effect         : centroid shift mid-stream → DRIFT fires')
    print(f'  Hotspot A      : {int(n_points*0.12)} pts, both peaks, always detected')
    print(f'  Hotspot B      : {int(n_points*0.08)} pts, morning — may appear as 2nd hotspot')
    print(f'  Hotspot C      : {int(n_points*0.06)} pts, evening — rotates with B')
    print(f'  Output         : {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--points', type=int, default=10000)
    parser.add_argument('--output', type=str, default='data/gps_data.csv')
    args = parser.parse_args()
    main(args.points, args.output)