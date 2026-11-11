from django.shortcuts import render
from rest_framework import permissions

from rest_framework.generics import ListCreateAPIView

from folders.models import Folder
from folders.serializers import FolderSerializer


class FolderListCreateAPIView(ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Folder.objects.all()
    serializer_class = FolderSerializer

# TODO: implement API for rename, delete, retrieve


