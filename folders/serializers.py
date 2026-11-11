from rest_framework import serializers

from folders.models import Folder


class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ('id', 'name', 'owner', 'created_at')

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return Folder.objects.create(**validated_data)