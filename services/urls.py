# services/urls.py
from rest_framework.routers import DefaultRouter
from services.views.access_control_view import UserServiceAccessViewSet

router = DefaultRouter()
router.register(r'access-control', UserServiceAccessViewSet, basename='access-control')

urlpatterns = router.urls
