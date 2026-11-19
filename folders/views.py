from rest_framework import permissions, status

from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

from folders.models import Folder
from folders.serializers import FolderSerializer


class FolderViewSet(ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Folder.objects.all()
    serializer_class = FolderSerializer

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        folder = self.get_object()
        folder_contains_file = folder.files.exists()
        if folder_contains_file:
            return Response({'detail':'Folder is not empty to remove'},
                            status=status.HTTP_409_CONFLICT)

        folder.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
