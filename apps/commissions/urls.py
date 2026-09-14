from django.urls import path
from .views import MyCommissionsAPIView

app_name = "commissions"

urlpatterns = [
    path("api/commissions/mine/", MyCommissionsAPIView.as_view(), name="my-commissions"),
]