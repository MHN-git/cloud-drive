from django.contrib.auth.models import User
from folders.models import Folder
from django.db import models

class Files(models.Model):
    name = models.CharField(max_length=200)
    size = models.BigIntegerField()
    status = models.CharField(max_length=200)
    storage_key = models.CharField(max_length=200)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
