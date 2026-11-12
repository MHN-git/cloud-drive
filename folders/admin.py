from django.contrib import admin
from folders.models import Folder

@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'created_at', 'updated_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'owner__username')
    ordering = ('name',)