from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from accounts.permissions import IsAdminUser, IsOwnerOrAdmin
from .models import Appointment
from .serializers import (
    AppointmentSerializer,
    AppointmentCreateSerializer,
    AppointmentAdminUpdateSerializer,
    CancelAppointmentSerializer,
)


class AppointmentListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields   = ['status', 'appointment_type', 'doctor', 'date']
    search_fields      = ['patient__first_name', 'patient__last_name', 'doctor__first_name', 'doctor__last_name']
    ordering_fields    = ['date', 'time', 'created_at', 'status']

    def get_queryset(self):
        user = self.request.user
        qs   = Appointment.objects.select_related('patient', 'doctor').all()
        if user.role == 'patient':
            return qs.filter(patient=user)
        return qs

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AppointmentCreateSerializer
        return AppointmentSerializer

    def perform_create(self, serializer):
        serializer.save(patient=self.request.user)

    def create(self, request, *args, **kwargs):
        if request.user.role != 'patient':
            return Response({'error': 'Only patients can book appointments.'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)


class AppointmentDetailView(generics.RetrieveAPIView):
    serializer_class   = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        qs   = Appointment.objects.select_related('patient', 'doctor').all()
        if user.role == 'patient':
            return qs.filter(patient=user)
        return qs


class AppointmentAdminUpdateView(generics.UpdateAPIView):
    serializer_class   = AppointmentAdminUpdateSerializer
    permission_classes = [IsAdminUser]
    queryset           = Appointment.objects.all()


class CancelAppointmentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            appointment = Appointment.objects.get(pk=pk, patient=request.user)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found.'}, status=status.HTTP_404_NOT_FOUND)

        if appointment.status in [Appointment.Status.COMPLETED, Appointment.Status.CANCELLED]:
            return Response(
                {'error': f'Cannot cancel a {appointment.get_status_display()} appointment.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CancelAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        appointment.status              = Appointment.Status.CANCELLED
        appointment.cancelled_at        = timezone.now()
        appointment.cancelled_by        = request.user
        appointment.cancellation_reason = serializer.validated_data.get('reason', '')
        appointment.save()

        return Response({'message': 'Appointment cancelled successfully.'})


class TodaysAppointmentsView(generics.ListAPIView):
    serializer_class   = AppointmentSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        today = timezone.now().date()
        return Appointment.objects.select_related('patient', 'doctor').filter(date=today).order_by('time')


class AppointmentCalendarView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        from django.db.models import Count

        year  = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))

        counts = (
            Appointment.objects
            .filter(date__year=year, date__month=month)
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        return Response({'year': year, 'month': month, 'data': list(counts)})