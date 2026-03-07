import csv

from shared_types import TrafficPoint
from st_clustering import run_clustering
from hotspot_validator import validate_hotspots


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

    print("\nValidating hotspots...")

    hotspot_info = validate_hotspots(clusters)

    for cid, info in hotspot_info.items():

        print(
            f"Cluster {cid} | size={info['cluster_size']} | "
            f"speed={info['avg_speed']:.1f} | "
            f"density={info['avg_density']:.1f} | "
            f"flow={info['avg_flow']:.1f} | "
            f"type={info['label']}"
        )


if __name__ == "__main__":
    main()