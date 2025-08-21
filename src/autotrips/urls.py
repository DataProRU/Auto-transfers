from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views.acceptance_report import AcceptanceReportViewSet, CarPhotoViewSet, DocPhotoViewSet, KeyPhotoViewSet
from .views.vehicle_bid import VehicleBidViewSet, VehicleTransporterViewset
from .views.vehicle_info import VehicleInfoViewSet, VehicleTypeViewSet

# Create a router and register the ViewSet
router = DefaultRouter()
router.register(r"reports", AcceptanceReportViewSet, basename="acceptance_report")
router.register(r"reports/(?P<report_id>\d+)/car-photos", CarPhotoViewSet, basename="car_image")
router.register(r"reports/(?P<report_id>\d+)/doc-photos", DocPhotoViewSet, basename="doc_image")
router.register(r"reports/(?P<report_id>\d+)/key-photos", KeyPhotoViewSet, basename="key_image")
router.register(r"vehicles", VehicleInfoViewSet, basename="vehicle_info")
router.register(r"vehicles-types", VehicleTypeViewSet, basename="vehicle-type")
router.register(r"bids", VehicleBidViewSet, basename="vehicle-bid")
router.register(r"transporters", VehicleTransporterViewset, basename="vehicle-transpoter")

urlpatterns = [
    # Include the router-generated URLs
    path("", include(router.urls)),
]
