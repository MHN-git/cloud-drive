import json

from django.core.management.base import BaseCommand
from django.conf import settings
from kafka import KafkaConsumer

from quota.models import Quota


class Command(BaseCommand):
    help = "consume quota recalculation events"

    def handle(self, *args, **options):
        consumer = KafkaConsumer(
            settings.KAFKA_QUOTA_RECALCULATE_TOPIC,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS.split(","),
            group_id='quota-consumer',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=False,
        )

        self.stdout.write("consume quota recalculation events started")

        try:
            for message in consumer:
                event = message.value
                owner_id = event['payload']['owner_id']

                Quota.recalculate_user_quota(owner_id)
                consumer.commit()

                self.stdout.write(f"quota recalculation for {owner_id}")

        finally:
            consumer.close()