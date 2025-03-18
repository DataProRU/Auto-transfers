from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views.acceptance_report import AcceptanceReportViewSet, CarPhotoViewSet, DocPhotoViewSet, KeyPhotoViewSet

# Create a router and register the ViewSet
router = DefaultRouter()
router.register(r"reports", AcceptanceReportViewSet, basename="acceptance_report")
router.register(r"reports/(?P<report_id>\d+)/car-photos", CarPhotoViewSet, basename="car_image")
router.register(r"reports/(?P<report_id>\d+)/doc-photos", DocPhotoViewSet, basename="doc_image")
router.register(r"reports/(?P<report_id>\d+)/key-photos", KeyPhotoViewSet, basename="key_image")

urlpatterns = [
    # Include the router-generated URLs
    path("", include(router.urls)),
]
