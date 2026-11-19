
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from files.models import Files
from folders.models import Folder
from quota.models import Quota


User = get_user_model()

@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "accounts-tests",
        }
    }
)

class FileUploadCreationTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="user1",
            password="StrongPass123!",
        )

        self.other_user = User.objects.create_user(
            username="user2",
            password="StrongPass123!",
        )

        self.quota = Quota.objects.create(
            owner=self.user,
            quota_limit_bytes=10 * 1024 * 1024,
        )

        self.folder = Folder.objects.create(
            name="Documents",
            owner=self.user,
        )

        self.other_folder = Folder.objects.create(
            name="Other Documents",
            owner=self.other_user,
        )

        self.client.force_authenticate(user=self.user)

        self.file_list_url = reverse("file-list")

    def test_create_upload_successfully(self):
        payload = {
            "name": "document.pdf",
            "declared_size_bytes": 1024,
            "folder": self.folder.id,
        }

        response = self.client.post(
            self.file_list_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        file_obj = Files.objects.get(id=response.data["id"])

        self.assertEqual(file_obj.name, "document.pdf")
        self.assertEqual(file_obj.owner, self.user)
        self.assertEqual(file_obj.folder, self.folder)
        self.assertEqual(file_obj.declared_size_bytes, 1024)
        self.assertEqual(file_obj.status, Files.Status.PENDING)
        self.assertIsNone(file_obj.size_bytes)

        self.quota.refresh_from_db()

        self.assertEqual(self.quota.reserved_bytes, 1024)
        self.assertEqual(self.quota.used_bytes, 0)

    def test_create_upload_with_insufficient_quota(self):
        payload = {
            "name": "large-file.zip",
            "declared_size_bytes": 11 * 1024 * 1024,
            "folder": self.folder.id,
        }

        response = self.client.post(
            self.file_list_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Files.objects.count(), 0)

        self.quota.refresh_from_db()

        self.assertEqual(self.quota.reserved_bytes, 0)

    def test_create_upload_with_zero_size(self):
        payload = {
            "name": "empty.pdf",
            "declared_size_bytes": 0,
            "folder": self.folder.id,
        }

        response = self.client.post(
            self.file_list_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Files.objects.count(), 0)

    def test_create_upload_in_another_users_folder(self):
        payload = {
            "name": "document.pdf",
            "declared_size_bytes": 1024,
            "folder": self.other_folder.id,
        }

        response = self.client.post(
            self.file_list_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Files.objects.count(), 0)

        self.quota.refresh_from_db()

        self.assertEqual(self.quota.reserved_bytes, 0)




from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.conf import settings

from files.models import Files
from files.management.commands.consume_upload_events import process_upload_event


class UploadConsumerTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="consumer_user",
            password="StrongPass123!",
        )

        self.folder = Folder.objects.create(
            name="Consumer Folder",
            owner=self.user,
        )

        self.file = Files.objects.create(
            name="document.pdf",
            declared_size_bytes=1024,
            folder=self.folder,
            owner=self.user,
        )

        self.event = {
            "event_id": "test-event-123",
            "event_type": "file.upload.complete",
            "payload": {
                "file_id": self.file.id,
                "owner_id": self.user.id,
                "storage_key": self.file.storage_key,
                "declared_size_bytes": 1024,
            },
        }

    @patch(
        "files.management.commands.consume_upload_events.publish_quota_recalculate"
    )
    @patch(
        "files.management.commands.consume_upload_events.invalidate_folder_files_cache"
    )
    @patch(
        "files.management.commands.consume_upload_events.get_minio_client"
    )
    def test_consumer_completes_upload_successfully(
        self,
        mock_get_client,
        mock_invalidate_cache,
        mock_publish_quota,
    ):
        mock_client = mock_get_client.return_value
        mock_client.stat_object.return_value = SimpleNamespace(size=1024)

        process_upload_event(self.event)

        self.file.refresh_from_db()

        self.assertEqual(self.file.status, Files.Status.READY)
        self.assertEqual(self.file.size_bytes, 1024)

        mock_client.stat_object.assert_called_once()
        mock_invalidate_cache.assert_called_once_with(
            owner_id=self.user.id,
            folder_id=self.folder.id,
        )
        mock_publish_quota.assert_called_once()

    @patch(
        "files.management.commands.consume_upload_events.publish_quota_recalculate"
    )
    @patch(
        "files.management.commands.consume_upload_events.invalidate_folder_files_cache"
    )
    @patch(
        "files.management.commands.consume_upload_events.get_minio_client"
    )
    def test_consumer_marks_file_failed_when_size_does_not_match(
        self,
        mock_get_client,
        mock_invalidate_cache,
        mock_publish_quota,
    ):
        mock_client = mock_get_client.return_value
        mock_client.stat_object.return_value = SimpleNamespace(size=2048)

        process_upload_event(self.event)

        self.file.refresh_from_db()

        self.assertEqual(self.file.status, Files.Status.FAILED)
        self.assertEqual(self.file.size_bytes, 2048)

        mock_client.remove_object.assert_called_once_with(
            settings.MINIO_BUCKET,
            self.file.storage_key,
        )

        mock_invalidate_cache.assert_called_once()
        mock_publish_quota.assert_called_once()

