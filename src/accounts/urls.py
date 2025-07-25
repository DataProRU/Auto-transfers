from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenVerifyView

from accounts.views.auth import CustomTokenObtainPairView, CustomTokenRefreshView
from accounts.views.register import ClientRegisterView, RegisterView
from accounts.views.user import CurrentUserViewSet, DocumentImageViewSet, UserViewSet

router = DefaultRouter()
router.register(r"users/current-user", CurrentUserViewSet, basename="current_user")
router.register(r"users/(?P<user_id>\d+)/documents", DocumentImageViewSet, basename="document_image")
router.register(r"users", UserViewSet, basename="users")

urlpatterns = [
    path("", include(router.urls)),
    path("register/", RegisterView.as_view(), name="register"),
    path("register/client/", ClientRegisterView.as_view(), name="client_register"),
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
]
