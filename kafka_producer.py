import csv
import json
import time

from kafka import KafkaProducer
from config import KAFKA_BOOTSTRAP, KAFKA_TOPIC


def create_producer():
    """
    Create Kafka producer instance.
    """
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    return producer


def stream_csv(file_path, producer, delay=0.01):
    """
    Stream CSV rows into Kafka topic.
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
    main()