from django.contrib import admin
from quota.models import Quota

@admin.register(Quota)
class QuotaAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'quota_limit_bytes', 'used_bytes', 'reserved_bytes', 'updated_at')
    search_fields = ('owner__username',)



        