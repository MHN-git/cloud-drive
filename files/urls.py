from django.urls import path

from files.views import *

urlpatterns = [
    path('', FileListCreateApiView.as_view(), name='file-list-create'),
    path('<int:pk>', FileRetrieveUpdateApiView.as_view(), name='file-retrieve-update'),
]