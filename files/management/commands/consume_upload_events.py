import json

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from kafka import KafkaConsumer

from files.minio_client import get_minio_client
from files.models import Files


def process_upload_event(event):
    payload = event['paylod']

    file_id = payload['file_id']
    owner_id = payload['owner_id']
    storage_key = payload['storage_key']
    declared_size = payload['declared_size_bytes']

    try:
        file_obj = Files.objects.get(pk=file_id, owner_id=owner_id, storage_key=storage_key)
    except Files.DoesNotExist:
        return

    if file_obj.status != Files.Status.PENDING:
        return

    client = get_minio_client()

    file_info = client.stat_object(settings.MINIO_BUCKET, storage_key)

    actual_size = file_info.size

    with transaction.atomic():
         file_obj = Files.objects.select_for_update().get(pk=file_id)

         if declared_size != actual_size:
             file_obj.status = Files.Status.FAILED
             file_obj.size_bytes = actual_size
             file_obj.save()
             client.remove_object(settings.MINIO_BUCKET, storage_key)
             return

         file_obj.size_bytes = actual_size
         file_obj.status = Files.Status.READY
         file_obj.save()




class Command(BaseCommand):
    help = 'consume and process upload completion event'

    def handle(self, *args, **options):
        consumer = KafkaConsumer(
            settings.KAFKA_UPLOAD_COMPLETED_TOPIC,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS.split(','),
            group_id="complete-upload-consumer",
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=False
        )

        self.stdout.write("upload consumer started")

        try:
            for message in consumer:
                event = message.value

                self.stdout.write(f"processing event: {event['event_id']}")
                process_upload_event(event)

                consumer.commit()

                self.stdout.write("event completed")

        finally :
            consumer.close()
