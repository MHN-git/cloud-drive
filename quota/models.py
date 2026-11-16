from django.db import models, transaction
from django.conf import settings
from django.db.models import Sum
from django.core.cache import cache

from files.models import Files


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

    @staticmethod
    def recalculate_user_quota(owner_id):
        with transaction.atomic():
            try:
                quota = Quota.objects.select_for_update().get(owner_id=owner_id)
            except Quota.DoesNotExist:
                return

            totals = Files.objects.filter(
                owner_id=owner_id,
                status=Files.Status.READY
            ).aggregate(total=Sum('size_bytes'))

            used_bytes = totals['total'] or 0

            reservations = Files.objects.filter(
                owner_id=owner_id,
                status=Files.Status.PENDING
            ).aggregate(reserved=Sum('declared_size_bytes'))

            reserved_bytes = reservations['reserved'] or 0

            quota.used_bytes = used_bytes
            quota.reserved_bytes = reserved_bytes
            quota.save()

        cache.delete(f'user:{owner_id}:quota')