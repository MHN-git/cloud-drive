from django.contrib.auth.models import User
from django.db import models

class Quota(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    quota_limit = models.BigIntegerField()
    used_bytes = models.BigIntegerField()
    reserved_bytes = models.BigIntegerField()

    def __str__(self):
        return self.quota_limit