import uuid
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from files.kafka_producer import publish_upload_complete, publish_quota_recalculate
from files.minio_client import get_minio_client
from files.models import Files
from files.permissions import FileRetrieveUpdatePermission
from files.serializers import FileSerializer
from files.cache_utils import get_folder_files_cache_key, invalidate_folder_files_cache

class FileViewSet(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  GenericViewSet):

    queryset = Files.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = FileSerializer

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

        # if user want to retrieve other user's file , we will give him 404.
        # we could use permission class, but  it will give 403. this proves to user that there is a file
        # ,but you can't access it. so 404 is better for less data leakage

    def perform_create(self, serializer):
        instance = serializer.save(owner=self.request.user)
        owner_id = instance.owner_id
        folder_id = instance.folder_id
        invalidate_folder_files_cache(owner_id=owner_id, folder_id=folder_id)

    def perform_update(self, serializer):
        instance = serializer.save()
        owner_id = instance.owner_id
        folder_id = instance.folder_id
        invalidate_folder_files_cache(owner_id=owner_id, folder_id=folder_id)

    def list(self, request, *args, **kwargs):
        folder_id = request.query_params.get("folder")
        if not folder_id:
            return super().list(request, *args, **kwargs)

        cache_key = get_folder_files_cache_key(owner_id=request.user.id,folder_id=folder_id)
        cached_data = cache.get(cache_key)
        if cached_data:
            print(cached_data)
            return Response(cached_data)

        data = self.filter_queryset(self.get_queryset(), folder=folder_id)
        serializer = self.get_serializer(data, many=True)
        cache.set(cache_key, serializer.data, timeout=300)

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        file_obj = self.get_object()

        owner_id = file_obj.owner_id
        folder_id = file_obj.folder_id
        file_id = file_obj.id
        storage_key = file_obj.storage_key

        file_status = file_obj.status
        if file_status != Files.Status.FAILED:
            minio_client = get_minio_client()
            minio_client.remove_object(settings.MINIO_BUCKET,storage_key)

        with transaction.atomic():
            file_obj = Files.objects.select_for_update().get(pk=file_id)
            file_obj.delete()

        invalidate_folder_files_cache(owner_id=owner_id, folder_id=folder_id)

        quota_event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "quota.recalculate",
            "occurred_at": timezone.now().isoformat(),
            "payload": {
                "owner_id": owner_id,
                "reason": "file_deleted",
                "file_id": file_id,
            },
        }

        publish_quota_recalculate(quota_event)
        return Response(status=status.HTTP_204_NO_CONTENT)


    def filter_queryset(self, queryset, **params):
        filtered_queryset =  queryset.filter(**params)
        if filtered_queryset.exists():
            return filtered_queryset
        else:
            raise ValidationError(detail={'detail': 'No Files matches the given query.'})

    @action(detail=True, methods=['post'], url_path='upload-url')
    def upload_url(self, request, pk):
        file_obj = self.get_object()

        if file_obj.status != Files.Status.PENDING:
            raise ValidationError("upload url can only be generated for pending files")

        client = get_minio_client()

        expires_in = settings.MINIO_PRESIGNED_URL_EXPIRY_SECONDS
        upload_url = client.presigned_put_object(bucket_name=settings.MINIO_BUCKET,
                                                 object_name=file_obj.storage_key,
                                                 expires=timedelta(seconds=expires_in),)

        return Response({'upload_url': upload_url,
                         'method': 'PUT',
                         'expires_in': expires_in,})


    @action(detail=True, methods=['post'], url_path='complete-upload')
    def complete_upload(self, request, pk):
        file_obj = self.get_object()

        if file_obj.status != Files.Status.PENDING:
            raise ValidationError("only pending files can be completed")

        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "file.upload.complete",
            "occurred_at":timezone.now().isoformat()    ,
            "payload": {
                "file_id":file_obj.id,
                "owner_id":file_obj.owner_id,
                "storage_key":file_obj.storage_key,
                "declared_size_bytes":file_obj.declared_size_bytes,
            }
        }

        publish_upload_complete(event)

        return Response({
            "message": "Upload completion event published.",
            "file_id": file_obj.id,
            "status": file_obj.status,
            })

    @action(detail=True, methods=['get'], url_path='download-url')
    def download_url(self, request, pk):
        file_obj = self.get_object()

        storage_key = file_obj.storage_key
        file_status = file_obj.status

        if file_status != Files.Status.READY:
            raise ValidationError("this file is not available for download")

        minio_client = get_minio_client()

        expires_in = settings.MINIO_PRESIGNED_URL_EXPIRY_SECONDS

        download_url = minio_client.presigned_get_object(
            bucket_name=settings.MINIO_BUCKET,
            object_name=file_obj.storage_key,
            expires=timedelta(seconds=expires_in),
        )

        return Response({
            'upload_url': download_url,
            'expires_in': expires_in,
        })

