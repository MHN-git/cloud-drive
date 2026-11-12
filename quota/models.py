from django.contrib.auth.models import User
from django.db import models
from django.conf import settings

def get_default_quota_bytes():
    return settings.DEFAULT_QUOTA_MB*1024*1024

class Quota(models.Model):
    owner = models.OneToOneField(settings.AUTH_USER_MODEL , on_delete=models.CASCADE, related_name='quota')
    quota_limit_bytes = models.PositiveBigIntegerField(default=get_default_quota_bytes)
    used_bytes = models.PositiveBigIntegerField(default=0)
    reserved_bytes = models.PositiveBigIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.owner} - Quota'