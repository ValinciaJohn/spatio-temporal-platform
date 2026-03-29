"""import csv
import json
import time

from kafka import KafkaProducer
from config import KAFKA_BOOTSTRAP, KAFKA_TOPIC


def create_producer():
    """
    # Create Kafka producer instance.
"""
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    return producer


def stream_csv(file_path, producer, delay=0.01):
    """
   # Stream CSV rows into Kafka topic.
"""

    with open(file_path, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            producer.send(KAFKA_TOPIC, value=row)

            print(f"[PRODUCED] {row['id']}")

            time.sleep(delay)

    producer.flush()
    
    
def main():
    file_path = "data/gps_data.csv"

    print("[PRODUCER] Starting producer...")

    producer = create_producer()

    stream_csv(file_path, producer)

    print("[PRODUCER] Streaming complete.")


if __name__ == "__main__":
    main()"""



import csv
import json
import time
import dataclasses

from shared_types import TrafficPoint

from kafka import KafkaProducer


def row_to_traffic_point(row: dict) -> TrafficPoint:
    """
    Converts a CSV row (dict from csv.DictReader) into a TrafficPoint.
    All numeric fields are cast from string to float.

    Expected CSV columns: id, lat, lon, timestamp, speed, density, flow
    """
    return TrafficPoint(
        id=row['id'],
        lat=float(row['lat']),
        lon=float(row['lon']),
        timestamp=float(row['timestamp']),
        speed=float(row['speed']),
        density=float(row['density']),
        flow=float(row['flow']),
        cluster_id=-1,
        is_anomaly=False,
        regime='unknown'
    )


def point_to_json(point: TrafficPoint) -> str:
    """
    Serializes a TrafficPoint to a JSON string.
    Uses dataclasses.asdict() to convert to dict first.
    """
    d = dataclasses.asdict(point)
    return json.dumps(d)


def create_producer(bootstrap_servers='localhost:9092'):
    """
    Creates and returns a KafkaProducer connected to the given broker.
    Value serializer encodes JSON strings to UTF-8 bytes.
    """
    if KafkaProducer is None:
        raise RuntimeError("kafka-python is not installed. Run: pip install kafka-python")

    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: v.encode('utf-8')
    )


def stream_dataset(
    filepath: str,
    topic: str = 'traffic_stream',
    speed_multiplier: int = 10,
    bootstrap_servers: str = 'localhost:9092'
) -> None:
    """
    Reads a CSV file row by row and streams each point to Kafka,
    simulating a real-time feed.

    speed_multiplier: higher = faster replay (10x means 10x faster than real time)
    Flushes every 50 rows. Prints progress every 100 rows.
    """
    producer = create_producer(bootstrap_servers)
    prev_timestamp = None
    count = 0

    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pt = row_to_traffic_point(row)

            # Simulate real-time delay between consecutive points
            if prev_timestamp is not None:
                delay = (pt.timestamp - prev_timestamp) / speed_multiplier
                if delay > 0:
                    time.sleep(delay)

            producer.send(topic, value=point_to_json(pt))
            prev_timestamp = pt.timestamp
            count += 1

            # Flush every 50 rows to ensure messages are sent
            if count % 50 == 0:
                producer.flush()

            # Progress update every 100 rows
            if count % 100 == 0:
                print(f'Sent {count} points...')

    producer.flush()
    print(f'Done. Total points sent: {count}')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Stream GPS data to Kafka')
    parser.add_argument('--file', required=True, help='Path to CSV data file')
    parser.add_argument('--speed', type=int, default=10, help='Speed multiplier (default: 10)')
    parser.add_argument('--topic', default='traffic_stream', help='Kafka topic name')
    args = parser.parse_args()

    stream_dataset(args.file, topic=args.topic, speed_multiplier=args.speed)