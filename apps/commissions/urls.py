from django.urls import path
from .views import MyCommissionsAPIView, my_commissions_page

app_name = "commissions"

urlpatterns = [
    path("api/commissions/mine/", MyCommissionsAPIView.as_view(), name="my-commissions"),
    path("commissions/", my_commissions_page, name="my-commissions-page"),
]