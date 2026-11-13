from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from files.models import Files
from files.permissions import FileRetrieveUpdatePermission
from files.serializers import FileSerializer


class FileListCreateApiView(ListCreateAPIView):
    queryset = Files.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = FileSerializer

    def get_queryset(self):

        return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):

        serializer.save(owner=self.request.user)

class FileRetrieveUpdateApiView(RetrieveUpdateAPIView):
    queryset = Files.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = FileSerializer

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)
        # if user want to retrieve other user's file , we will give him 404.
        # we could use permission class, but  it will give 403. this proves to user that there is a file
        # ,but you can't access it. so 404 is better for less data leakage


#TODO: both views bodies are similar to each other. retrieve and list use different Get method with same name but with different logic \
# so i can't gather them in one view class . solution is using viewSet. fix this whenever you learn about it.
