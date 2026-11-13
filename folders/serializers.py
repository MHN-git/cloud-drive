from rest_framework import serializers

from folders.models import Folder


class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ('id', 'name', 'owner', 'created_at', 'updated_at')
        read_only_fields = ('owner',)