from django.conf import settings
from django.core.management.base import BaseCommand

from files.minio_client import get_minio_client

class Command(BaseCommand):
    help = 'Ensure Minio bucket exists'

    def handle(self, *args, **options):
        client = get_minio_client()
        bucket_name = settings.MINIO_BUCKET

        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            self.stdout.write(self.style.SUCCESS(f'bucket {bucket_name} created'))
        else:
            self.stdout.write(self.style.WARNING(f'bucket {bucket_name} already exists'))

