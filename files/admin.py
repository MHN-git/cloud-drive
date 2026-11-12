from django.contrib import admin
from files.models import Files

@admin.register(Files)
class FileAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'declared_size_bytes', 'size_bytes', 'owner', 'folder', 'status','created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'owner__username', 'storage_key')
    ordering = ('-created_at',)

