from django.urls import path
from accounts.views import *

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path('signup/', SignUpAPIView.as_view(), name='signup'),
    path('login/', TokenObtainPairView.as_view(), name='login'),

]