from django.urls import path

from accounts.views.auth import CustomTokenObtainPairView
from accounts.views.register import RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
]
