import json
from typing import List

from shared_types import TrafficPoint

try:
    from kafka import KafkaConsumer
except ImportError:
    KafkaConsumer = None

# Module-level singleton consumer — created once and reused
_consumer = None


def json_to_traffic_point(json_str: str) -> TrafficPoint:
    """
    Deserializes a JSON string back into a TrafficPoint.
    Uses **d to unpack all fields from the dict directly.
    """
    d = json.loads(json_str)
    return TrafficPoint(**d)


def create_consumer(
    topic: str = 'traffic_stream',
    group_id: str = 'mobility_pipeline',
    bootstrap_servers: str = 'localhost:9092'
) -> 'KafkaConsumer':
    """
    Creates and returns a KafkaConsumer subscribed to the given topic.
    auto_offset_reset='earliest' means it reads from the beginning if
    no committed offset exists for this group_id.
    consumer_timeout_ms=1000 means poll() returns after 1 second if no messages.
    """
    if KafkaConsumer is None:
        raise RuntimeError("kafka-python is not installed. Run: pip install kafka-python")

    return KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id=group_id,
        value_deserializer=lambda m: m.decode('utf-8'),
        consumer_timeout_ms=1000
    )


def consume_batch(consumer, batch_size: int = 200, timeout_ms: int = 1000) -> List[TrafficPoint]:
    """
    Polls Kafka for up to batch_size messages within timeout_ms.
    Flattens all partition records into a single list of TrafficPoints.
    Returns empty list if no messages available.
    """
    records = consumer.poll(timeout_ms=timeout_ms, max_records=batch_size)

    points = []
    for partition, messages in records.items():
        for msg in messages:
            try:
                point = json_to_traffic_point(msg.value)
                points.append(point)
            except Exception as e:
                print(f'[CONSUMER] Skipping malformed message: {e}')

    return points


def get_next_batch(batch_size: int = 200) -> List[TrafficPoint]:
    """
    MAIN EXPORT — called by pipeline.py every cycle.
    Maintains a module-level singleton consumer so the connection
    is created once and reused across calls.
    Returns a list of TrafficPoints (may be empty if no new messages).
    """
    global _consumer

    if _consumer is None:
        _consumer = create_consumer()

    return consume_batch(_consumer, batch_size)


if __name__ == '__main__':
    print('[CONSUMER] Connecting to Kafka...')
    consumer = create_consumer()
    print('[CONSUMER] Waiting for messages (up to 5 seconds)...')

    batch = consume_batch(consumer, batch_size=5, timeout_ms=5000)

    if batch:
        print(f'[CONSUMER] Received {len(batch)} points. First point:')
        print(f'  id={batch[0].id}, lat={batch[0].lat}, speed={batch[0].speed}')
        print('[CONSUMER] Round-trip test PASSED!')
    else:
        print('[CONSUMER] No messages received.')
        print('  Make sure kafka_producer.py has sent some messages first.')

    consumer.close()