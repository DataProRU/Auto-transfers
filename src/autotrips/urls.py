from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views.acceptance_report import AcceptanceReportViewSet

# Create a router and register the ViewSet
router = DefaultRouter()
router.register(r"reports", AcceptanceReportViewSet, basename="acceptancereport")

urlpatterns = [
    # Include the router-generated URLs
    path("", include(router.urls)),
]
