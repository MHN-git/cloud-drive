from django.db import transaction
from rest_framework import serializers

from files.models import Files
from folders.models import Folder
from quota.models import Quota


class FileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Files
        fields = ('id', 'name', 'declared_size_bytes',
                  'size_bytes', 'owner', 'folder',
                  'status', 'storage_key', 'created_at', 'updated_at')

        read_only_fields = ('size_bytes', 'owner',
                            'status', 'storage_key')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get('request')
        if self.instance is None:  #list - create
            self.fields['folder'].queryset = Folder.objects.filter(owner=request.user)
        else:                      # retrieve - update
            self.fields['folder'].read_only = True
            self.fields['declared_size_bytes'].read_only = True


    def validate_name(self, name):
        name = name.strip()
        if not name:
            raise serializers.ValidationError(detail='File name cannot be empty')

        return name

    def validate_declared_size_bytes(self, declared_size_bytes):
        if declared_size_bytes <= 0:
            raise serializers.ValidationError(detail='Declared size must be greater than 0')

        return declared_size_bytes

    def create(self, validated_data):
        owner = self.context.get('request').user
        requested_size = validated_data.get('declared_size_bytes')

        with transaction.atomic():
            quota = Quota.objects.select_for_update().get(owner=owner)
            available_bytes = quota.quota_limit_bytes - quota.used_bytes - quota.reserved_bytes

            if requested_size > available_bytes:
                raise serializers.ValidationError(detail=
                {"declared_size_bytes": (
                    f"Insufficient storage space. "
                    f"Available: {available_bytes} bytes.")}
                )

            quota.reserved_bytes += requested_size
            quota.save()

            file = Files(**validated_data)
            file.save()

            return file
