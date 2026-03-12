from django.db.models import Sum, Count
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminUser
from .models import Payment
from .serializers import PaymentSerializer, PaymentUpdateSerializer


class PaymentListView(generics.ListAPIView):
    serializer_class   = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields   = ['status', 'method']
    search_fields      = ['invoice_number', 'appointment__patient__first_name', 'appointment__patient__last_name']
    ordering_fields    = ['created_at', 'amount', 'paid_at']

    def get_queryset(self):
        user = self.request.user
        qs   = Payment.objects.select_related('appointment__patient', 'appointment__doctor').all()
        if user.role == 'patient':
            return qs.filter(appointment__patient=user)
        return qs


class PaymentDetailView(generics.RetrieveAPIView):
    serializer_class   = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs   = Payment.objects.select_related('appointment__patient', 'appointment__doctor').all()
        if user.role == 'patient':
            return qs.filter(appointment__patient=user)
        return qs


class PaymentAdminUpdateView(generics.UpdateAPIView):
    serializer_class   = PaymentUpdateSerializer
    permission_classes = [IsAdminUser]
    queryset           = Payment.objects.all()


class RevenueReportView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date   = request.query_params.get('end_date')

        qs = Payment.objects.filter(status=Payment.Status.PAID)

        if start_date:
            qs = qs.filter(paid_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(paid_at__date__lte=end_date)

        total_revenue = qs.aggregate(total=Sum('amount'))['total'] or 0
        total_paid    = qs.count()

        daily = (
            qs.values('paid_at__date')
            .annotate(revenue=Sum('amount'), count=Count('id'))
            .order_by('paid_at__date')
        )

        by_method = (
            qs.values('method')
            .annotate(total=Sum('amount'), count=Count('id'))
        )

        return Response({
            'total_revenue':    total_revenue,
            'total_paid_count': total_paid,
            'daily_breakdown':  list(daily),
            'by_method':        list(by_method),
        })