import random
import math
import csv
import os


def generate_cluster_points(centre_lat, centre_lon, n, base_speed, label, start_ts):
    """
    Generate clustered GPS traffic points around a centre.
    Returns list of dictionaries matching CSV schema.
    """

    results = []

    for i in range(n):
        # Spatial spread (Gaussian noise)
        lat = centre_lat + random.gauss(0, 0.0015)
        lon = centre_lon + random.gauss(0, 0.0015)

        # Temporal progression
        timestamp = start_ts + random.uniform(0, 300)
        

        # Speed variation around base speed
        speed = max(1.0, min(120.0, base_speed + random.gauss(0, 2)))
        # Density inversely related to speed
        base_density = 150 / max(base_speed, 1)
        density = max(1.0, min(150.0, base_density + random.gauss(0, 3)))
        
        # Flow proportional to speed × density
        base_flow = (base_speed * base_density) / 60
        flow = max(0.1, min(60.0, base_flow + random.gauss(0, 1)))
        
        point_id = f"{label}_pt_{i:04d}"

        results.append({
            "id": point_id,
            "lat": str(lat),
            "lon": str(lon),
            "timestamp": str(timestamp),
            "speed": str(speed),
            "density": str(density),
            "flow": str(flow),
        })

    return results

def generate_noise_points(n, lat_range, lon_range, start_ts):
    """
    Generate random noise traffic points scattered across the study area.
    Returns list of dictionaries matching CSV schema.
    """

    results = []

    for i in range(n):
        lat = random.uniform(*lat_range)
        lon = random.uniform(*lon_range)
        
        timestamp = start_ts + random.uniform(0, 86400)  # spread over 24 hours
    
        speed = random.uniform(20, 80)
        density = random.uniform(5, 40)
        flow = random.uniform(5, 30)

        point_id = f"noise_pt_{i:04d}"

        results.append({
            "id": point_id,
            "lat": str(lat),
            "lon": str(lon),
            "timestamp": str(timestamp),
            "speed": str(speed),
            "density": str(density),
            "flow": str(flow),
        })

    return results

def write_csv(rows, filepath):
    """
    Write generated rows to CSV file.
    """

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "lat", "lon", "timestamp", "speed", "density", "flow"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"[DATA] Written {len(rows)} rows to {filepath}")
    
def main(n_points=5000, n_clusters=6, output="data/gps_data.csv"):
    """
    Generate full synthetic traffic dataset.
    """

    # Beijing area cluster centres
    centres = [
        (39.92, 116.39),
        (39.95, 116.44),
        (39.88, 116.50),
        (39.91, 116.35),
        (39.98, 116.47),
        (39.85, 116.42),
    ]

    base_speeds = [15, 8, 45, 60, 20, 70]
    cluster_labels = ["cong_A", "cong_B", "slow_C", "free_D", "slow_E", "free_F"]

    cluster_points_total = int(n_points * 0.8)
    noise_count = n_points - cluster_points_total

    base_pts = cluster_points_total // n_clusters
    remainder = cluster_points_total % n_clusters

    start_ts = 1700000000.0

    all_rows = []

    # Generate clustered traffic
    for i, centre in enumerate(centres):
        pts_for_this_cluster = base_pts + (1 if i < remainder else 0)

        all_rows += generate_cluster_points(
            centre[0],
            centre[1],
            pts_for_this_cluster,
            base_speeds[i],
            cluster_labels[i],
            start_ts
    )

    # Generate noise
    all_rows += generate_noise_points(
        noise_count,
        (39.80, 40.05),
        (116.25, 116.65),
        start_ts
    )

    random.shuffle(all_rows)

    write_csv(all_rows, output)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--points", type=int, default=5000)
    parser.add_argument("--clusters", type=int, default=6)
    parser.add_argument("--output", type=str, default="data/gps_data.csv")

    args = parser.parse_args()

    main(args.points, args.clusters, args.output)