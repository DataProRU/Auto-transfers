from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views.auth import CustomTokenObtainPairView
from accounts.views.register import RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
