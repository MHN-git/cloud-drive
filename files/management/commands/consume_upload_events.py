import json
import uuid

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from kafka import KafkaConsumer

from files.kafka_producer import publish_quota_recalculate
from files.minio_client import get_minio_client
from files.models import Files
from files.cache_utils import invalidate_folder_files_cache

def process_upload_event(event):
    payload = event['payload']

    file_id = payload['file_id']
    owner_id = payload['owner_id']
    storage_key = payload['storage_key']
    declared_size = payload['declared_size_bytes']

    client = get_minio_client()

    with transaction.atomic():
        try:
            file_obj = Files.objects.get(pk=file_id, owner_id=owner_id, storage_key=storage_key)
        except Files.DoesNotExist:
            return

    if file_obj.status == Files.Status.PENDING:
        file_info = client.stat_object(settings.MINIO_BUCKET, storage_key)
        actual_size = file_info.size

        with transaction.atomic():
            try:
                file_obj = Files.objects.select_for_update().get(pk=file_id)
            except Files.DoesNotExist:
                return

            file_obj.size_bytes = actual_size

            if declared_size != actual_size:
                file_obj.status = Files.Status.FAILED
            else:
                file_obj.status = Files.Status.READY

            file_obj.save()

            final_status = file_obj.status

        invalidate_folder_files_cache(owner_id=owner_id, folder_id=file_obj.folder_id)

    if final_status == Files.Status.FAILED:
        client.remove_object(
            settings.MINIO_BUCKET,
            storage_key,
        )

    quota_event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "quota.recalculate",
        "occurred_at": timezone.now().isoformat(),
        "payload": {
            "owner_id": owner_id,
            "reason": "upload_completed",
            "file_id": file_id,
        },
    }
    publish_quota_recalculate(quota_event)


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
    