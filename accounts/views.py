from rest_framework import permissions
from rest_framework.generics import CreateAPIView

from accounts.serializers import SignUpSerializer

class SignUpAPIView(CreateAPIView):
    serializer_class = SignUpSerializer


# class LoginAPIView(APIView):
#     serializer_class = LoginSerializer
#
#     def Post(self,request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         return
#
#     def get_serializer(self, *args, **kwargs):
#         serializer_class = self.get_serializer_class()
#         kwargs.setdefault('context', {'request', self.request})
#         return serializer_class(*args, **kwargs)
#
#     def get_serializer_class(self):
#         return self.serializer_class
#
#
#
