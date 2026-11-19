from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from folders.models import Folder
from files.models import Files


User = get_user_model()


class FolderAPITests(TestCase):

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

        self.client.force_authenticate(user=self.user)

        self.folder_list_url = reverse("folder-list")

    def test_create_folder(self):
        response = self.client.post(
            self.folder_list_url,
            {"name": "My Documents"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "My Documents")
        self.assertEqual(response.data["owner"], self.user.id)

        self.assertTrue(
            Folder.objects.filter(
                name="My Documents",
                owner=self.user,
            ).exists()
        )

    def test_update_folder(self):
        folder = Folder.objects.create(
            name="Old Name",
            owner=self.user,
        )

        response = self.client.patch(
            reverse("folder-detail", args=[folder.id]),
            {"name": "New Name"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        folder.refresh_from_db()
        self.assertEqual(folder.name, "New Name")

    def test_delete_empty_folder(self):
        folder = Folder.objects.create(
            name="Empty Folder",
            owner=self.user,
        )

        response = self.client.delete(
            reverse("folder-detail", args=[folder.id])
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Folder.objects.filter(id=folder.id).exists())

    def test_cannot_delete_non_empty_folder(self):
        folder = Folder.objects.create(
            name="Non Empty Folder",
            owner=self.user,
        )

        Files.objects.create(
            name="document.pdf",
            declared_size_bytes=1024,
            folder=folder,
            owner=self.user,
        )

        response = self.client.delete(
            reverse("folder-detail", args=[folder.id])
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Folder.objects.filter(id=folder.id).exists())

    def test_user_cannot_access_another_users_folder(self):
        folder = Folder.objects.create(
            name="Private Folder",
            owner=self.other_user,
        )

        response = self.client.get(
            reverse("folder-detail", args=[folder.id])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_folder_list_contains_only_current_users_folders(self):
        own_folder = Folder.objects.create(
            name="My Folder",
            owner=self.user,
        )

        Folder.objects.create(
            name="Other Folder",
            owner=self.other_user,
        )

        response = self.client.get(self.folder_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = [item["id"] for item in response.data]

        self.assertIn(own_folder.id, returned_ids)
        self.assertEqual(len(returned_ids), 1)
