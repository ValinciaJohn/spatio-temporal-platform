import csv
import json
import time
import dataclasses

from shared_types import TrafficPoint
from config import KAFKA_BATCH_SIZE


try:
    from kafka import KafkaProducer
except ImportError:
    KafkaProducer = None


def row_to_traffic_point(row: dict) -> TrafficPoint:
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
    return json.dumps(dataclasses.asdict(point))


def create_producer(bootstrap_servers='localhost:9092'):
    if KafkaProducer is None:
        raise RuntimeError("kafka-python not installed. Run: pip install kafka-python")

    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: v.encode('utf-8'),
        acks=1,              # wait for leader acknowledgment
        retries=3,           # retry on failure
        linger_ms=10,        # small batch delay for efficiency
        batch_size=16384,    # 16KB batches
    )


def stream_dataset(
    filepath: str,
    topic: str = 'traffic_stream',
    speed_multiplier: int = 10,
    bootstrap_servers: str = 'localhost:9092'
) -> None:

    print("[PRODUCER] Connecting to Kafka...")
    producer = create_producer(bootstrap_servers)
    print("[PRODUCER] Connected.")

    count = 0
    failed = 0
    start_time = time.time()

    print("[PRODUCER] Starting stream...")

    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                pt = row_to_traffic_point(row)
                producer.send(topic, value=point_to_json(pt))
                count += 1

                # Flush every 200 messages to ensure delivery
                if count % KAFKA_BATCH_SIZE == 0:
                    producer.flush()
                    elapsed = time.time() - start_time
                    rate = round(count / max(elapsed, 1), 1)
                    print(f"[PRODUCER] {count} sent | {rate} msg/sec")

                    # Write throughput to shared state if available
                    try:
                        from state_store import APP_STATE
                        APP_STATE['throughput'] = rate
                    except Exception:
                        pass

            except Exception as e:
                failed += 1
                print(f"[PRODUCER ERROR] Row {count}: {e}")

    # Final flush — ensure all remaining messages are sent
    producer.flush()

    elapsed = time.time() - start_time
    print(f"[PRODUCER] Done. Sent: {count} | Failed: {failed} | "
          f"Time: {elapsed:.1f}s | Avg: {round(count/max(elapsed,1),1)} msg/sec")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Stream GPS data to Kafka')
    parser.add_argument('--file', required=True, help='Path to CSV data file')
    parser.add_argument('--topic', default='traffic_stream', help='Kafka topic name')
    args = parser.parse_args()

    stream_dataset(args.file, topic=args.topic)