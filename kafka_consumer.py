import json
from typing import List
from shared_types import TrafficPoint

try:
    from kafka import KafkaConsumer
except ImportError:
    KafkaConsumer = None

# ── Module-level singleton — ONE consumer, kept alive ─────────────────────
_consumer = None


def json_to_traffic_point(json_str: str) -> TrafficPoint:
    d = json.loads(json_str)
    return TrafficPoint(**d)


def _get_consumer():
    """
    Returns the module-level singleton consumer.
    Creates it on first call. Never closes it between batches.
    This is critical — closing and recreating causes offset commit issues.
    """
    global _consumer
    if _consumer is None:
        if KafkaConsumer is None:
            raise RuntimeError("kafka-python not installed. pip install kafka-python")

        import time
        # Use timestamp-based group_id so every run starts fresh
        # This means we always read from the beginning on each pipeline run
        unique_group = f"pipeline_{int(time.time())}"

        print(f"[CONSUMER] Creating consumer with group: {unique_group}")

        _consumer = KafkaConsumer(
            'traffic_stream',
            bootstrap_servers='localhost:9092',
            auto_offset_reset='earliest',      # always read from start
            enable_auto_commit=False,           # don't save offsets
            group_id=unique_group,
            value_deserializer=lambda m: m.decode('utf-8'),
            consumer_timeout_ms=5000,           # wait up to 5s for messages
            fetch_min_bytes=1,
            fetch_max_wait_ms=500,
        )
        print("[CONSUMER] Consumer ready.")
    return _consumer


def get_next_batch(batch_size: int = 500) -> List[TrafficPoint]:
    """
    MAIN EXPORT — called by pipeline.py every cycle.
    Uses persistent consumer — never closes between calls.
    """
    consumer = _get_consumer()

    records = consumer.poll(
        timeout_ms=5000,
        max_records=batch_size
    )

    total = sum(len(v) for v in records.values())
    print(f"[CONSUMER] Polled {total} messages")

    points = []
    for partition, messages in records.items():
        for msg in messages:
            try:
                points.append(json_to_traffic_point(msg.value))
            except Exception as e:
                print(f"[CONSUMER] Skipping malformed message: {e}")

    return points


def close_consumer():
    """Call this on shutdown if needed."""
    global _consumer
    if _consumer:
        _consumer.close()
        _consumer = None


if __name__ == '__main__':
    print('[CONSUMER] Testing connection...')
    batch = get_next_batch(batch_size=5)
    if batch:
        print(f'[CONSUMER] Got {len(batch)} points. First: id={batch[0].id}')
        print('[CONSUMER] TEST PASSED')
    else:
        print('[CONSUMER] No messages. Run producer first.')
    close_consumer()