from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views.auth import CustomTokenObtainPairView
from accounts.views.register import RegisterView
from accounts.views.user import CurrentUserViewSet, DocumentImageViewSet

router = DefaultRouter()
router.register(r"users/current-user", CurrentUserViewSet, basename="current_user")
router.register(r"users/(?P<user_id>\d+)/documents", DocumentImageViewSet, basename="document_image")

urlpatterns = [
    path("", include(router.urls)),
    path("register/", RegisterView.as_view(), name="register"),
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
