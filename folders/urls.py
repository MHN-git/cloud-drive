from django.urls import path

from folders.views import *

urlpatterns = [
    path('', FolderListCreateAPIView.as_view(), name='folder-list-create'),
    path('<int:pk>', FolderRetrieveUpdateDestroyAPIView.as_view(), name='folder-retrieve-update-delete'),
]