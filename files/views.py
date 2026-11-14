from datetime import timedelta

from django.conf import settings
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from files.minio_client import get_minio_client
from files.models import Files
from files.permissions import FileRetrieveUpdatePermission
from files.serializers import FileSerializer



class FileViewSet(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
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
        serializer.save(owner=self.request.user)

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


