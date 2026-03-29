import csv

from shared_types import TrafficPoint
from st_clustering import run_clustering
from visualizer import visualize_clusters


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

    print("Running clustering...")

    updated_points, clusters = run_clustering(points)

    print("Generating map...")

    visualize_clusters(updated_points)


if __name__ == "__main__":
    main()