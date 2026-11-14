import json

from kafka import KafkaProducer
from django.conf import settings

def get_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS.split(","),
        value_serializer=lambda m: json.dumps(m).encode("utf-8"),
        acks="all",
        retries=5,
    )

def publish_upload_complete(event):
    producer = get_kafka_producer()

    try:
        future = producer.send(
            topic=settings.KAFKA_UPLOAD_COMPLETED_TOPIC,
            value=event
        )

        future.get(timeout=10)

    finally:
        producer.close()

