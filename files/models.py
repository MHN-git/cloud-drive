import uuid

from django.conf import settings
from django.core.exceptions import ValidationError

from folders.models import Folder
from django.db import models

def generate_storage_key():
    return uuid.uuid4().hex

class Files(models.Model):

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        READY   = 'ready'  , 'Ready'
        FAILED  = 'failed' , 'Failed'

    name = models.CharField(max_length=200)
    declared_size_bytes = models.PositiveBigIntegerField()
    size_bytes = models.PositiveBigIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    storage_key = models.CharField(max_length=255, unique=True  ,default=generate_storage_key)
    folder = models.ForeignKey(Folder, on_delete=models.PROTECT, related_name='files')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='files')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['owner', 'folder']),
            models.Index(fields=['owner', 'status'])
        ]

    def clean(self):
        if self.folder_id and self.owner_id:
            if self.folder.owner_id != self.owner_id:
                raise ValidationError('The selected folder does not belong to this user')

    def __str__(self):
        return self.name
