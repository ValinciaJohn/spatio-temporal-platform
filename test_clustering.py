import csv

from shared_types import TrafficPoint
from st_clustering import run_clustering


def load_points(csv_file):
    points = []

    with open(csv_file, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            p = TrafficPoint(
                id=row["id"],
                lat=float(row["lat"]),
                lon=float(row["lon"]),
                timestamp=float(row["timestamp"]),
                speed=float(row["speed"]),
                density=float(row["density"]),
                flow=float(row["flow"]),
            )

            points.append(p)

    return points


def main():
    print("Loading dataset...")

    points = load_points("data/gps_data.csv")

    print(f"Loaded {len(points)} points")

    print("Running clustering...")

    updated_points, clusters = run_clustering(points)

    print(f"\nClusters found: {len(clusters)}")

    for cid, cluster in clusters.items():
        print(f"Cluster {cid} → {len(cluster.points)} points")

    noise_count = sum(1 for p in updated_points if p.cluster_id == -1)

    print(f"\nNoise points: {noise_count}")


if __name__ == "__main__":
    main()