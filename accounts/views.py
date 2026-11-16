from rest_framework import permissions
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from accounts.serializers import SignUpSerializer
from quota.services import get_user_quota_data


class SignUpAPIView(CreateAPIView):
    serializer_class = SignUpSerializer


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, *args, **kwargs):
        user = self.request.user
        quota_data = get_user_quota_data(user.id)
        response = {"id":user.id,
                    "username":user.username,
                    "quota": quota_data,
                    }
        return Response(response)


