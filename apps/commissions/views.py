from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import CommissionRecord
from .serializers import CommissionRecordSerializer


class MyCommissionsAPIView(generics.ListAPIView):
    serializer_class = CommissionRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CommissionRecord.objects.filter(
            user=self.request.user
        ).select_related("project")