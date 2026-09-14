from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Sum
from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import is_super_admin, is_engineer
from .models import CommissionRecord
from .serializers import CommissionRecordSerializer


class MyCommissionsAPIView(generics.ListAPIView):
    serializer_class = CommissionRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Engineers do not receive commissions — block API access
        if is_engineer(self.request.user):
            from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
            raise DRFPermissionDenied("Engineers do not have commission records.")
        qs = CommissionRecord.objects.select_related("project", "user")
        if self.request.query_params.get("all") == "1" and is_super_admin(self.request.user):
            return qs
        return qs.filter(user=self.request.user)


@login_required
def my_commissions_page(request):
    # Engineers do not receive commissions
    if is_engineer(request.user):
        raise PermissionDenied("Engineers do not have access to commission records.")

    showing_all = request.GET.get("view") == "all" and is_super_admin(request.user)
    qs = CommissionRecord.objects.select_related("project", "user").order_by("-created_at")
    if not showing_all:
        qs = qs.filter(user=request.user)

    totals = qs.aggregate(total=Sum("commission_amount"), sales=Sum("sale_amount"))
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "commissions/my_commissions.html",
        {
            "page_obj": page_obj,
            "showing_all": showing_all,
            "total_commission": totals["total"] or 0,
            "total_sales": totals["sales"] or 0,
            "record_count": paginator.count,
        },
    )