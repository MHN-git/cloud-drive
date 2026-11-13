from django.shortcuts import render
from rest_framework import permissions, status

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response

from folders.models import Folder
from folders.permissions import FolderRUDPermission
from folders.serializers import FolderSerializer


class FolderListCreateAPIView(ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Folder.objects.all()
    serializer_class = FolderSerializer

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FolderRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Folder.objects.all()
    serializer_class = FolderSerializer

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user).order_by('-created_at')
        # using this for giving 404 if user want to access other user's file.(by using permission class it will give 403)

    def destroy(self, request, *args, **kwargs):
        folder = self.get_object()
        folder_contains_file = folder.files.exists()
        if folder_contains_file:
            return Response({'detail':'Folder is not empty to remove'},
                            status=status.HTTP_409_CONFLICT)

        folder.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


    #TODO: both views bodies are similar to each other. retrieve and list use different Get method with same name but with different logic \
    # so i can't gather them in one view class . solution is using viewSet. fix this whenever you learn about it.
