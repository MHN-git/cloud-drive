from rest_framework.routers import DefaultRouter

from files.views import FileViewSet

router = DefaultRouter()
router.register('files', FileViewSet, basename='file')

urlpatterns = router.urls