import datetime
from rest_framework import generics, status, parsers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdminUser, IsAdminOrReadOnly
from .models import Doctor, DoctorSchedule
from .serializers import (
    DoctorSerializer,
    DoctorWriteSerializer,
    DoctorScheduleSerializer,
    DoctorPhotoUploadSerializer,
    AvailableSlotsSerializer,
)


class DoctorListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields   = ['specialty', 'status']
    search_fields      = ['first_name', 'last_name', 'specialty']
    ordering_fields    = ['last_name', 'consultation_fee']
    # Accept both JSON and multipart (file upload) on create
    parser_classes     = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DoctorWriteSerializer
        return DoctorSerializer

    def get_queryset(self):
        qs = Doctor.objects.prefetch_related('schedules').all()
        if not (self.request.user.is_authenticated and self.request.user.role == 'admin'):
            qs = qs.filter(status=Doctor.Status.ACTIVE)
        return qs

    def get_serializer_context(self):
        # Always pass request so photo_url can build absolute URIs
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class DoctorDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Doctor.objects.prefetch_related('schedules').all()
    permission_classes = [IsAdminOrReadOnly]
    parser_classes     = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return DoctorWriteSerializer
        return DoctorSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def destroy(self, request, *args, **kwargs):
        doctor = self.get_object()
        doctor.status = Doctor.Status.INACTIVE
        doctor.save()
        return Response({'message': f'{doctor.full_name} deactivated.'}, status=status.HTTP_200_OK)


class DoctorPhotoUploadView(APIView):
    """
    PATCH /api/v1/doctors/<pk>/photo/
    Upload or replace a doctor's profile photo.
    Send as multipart/form-data with field name 'photo'.
    Admin only.
    """
    permission_classes = [IsAdminUser]
    parser_classes     = [parsers.MultiPartParser, parsers.FormParser]

    def patch(self, request, pk):
        doctor = generics.get_object_or_404(Doctor, pk=pk)
        serializer = DoctorPhotoUploadSerializer(
            doctor,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        # Delete old photo from Cloudinary before saving new one (best practice)
        if doctor.photo:
            try:
                doctor.photo.delete(save=False)
            except Exception:
                pass  # Don't fail if old photo can't be deleted

        serializer.save()
        return Response({
            'message': 'Photo uploaded successfully.',
            'photo_url': serializer.data.get('photo_url'),
        }, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        """DELETE /api/v1/doctors/<pk>/photo/ — remove a doctor's photo."""
        doctor = generics.get_object_or_404(Doctor, pk=pk)
        if not doctor.photo:
            return Response({'message': 'No photo to delete.'}, status=status.HTTP_200_OK)

        try:
            doctor.photo.delete(save=False)
        except Exception:
            pass

        doctor.photo = None
        doctor.save()
        return Response({'message': 'Photo removed successfully.'}, status=status.HTTP_200_OK)


class DoctorScheduleView(generics.ListCreateAPIView):
    serializer_class   = DoctorScheduleSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return DoctorSchedule.objects.filter(doctor_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        doctor = generics.get_object_or_404(Doctor, pk=self.kwargs['pk'])
        serializer.save(doctor=doctor)


class DoctorScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = DoctorScheduleSerializer
    permission_classes = [IsAdminUser]
    queryset           = DoctorSchedule.objects.all()
    lookup_url_kwarg   = 'schedule_id'


class DoctorAvailableSlotsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        serializer = AvailableSlotsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        date   = serializer.validated_data['date']
        doctor = generics.get_object_or_404(Doctor, pk=pk, status=Doctor.Status.ACTIVE)

        day_of_week = date.weekday()
        try:
            schedule = doctor.schedules.get(day_of_week=day_of_week, is_available=True)
        except DoctorSchedule.DoesNotExist:
            return Response({'available_slots': [], 'message': 'Doctor not available on this day.'})

        all_slots = self._generate_slots(
            schedule.start_time, schedule.end_time, schedule.slot_duration_minutes
        )

        from appointments.models import Appointment
        booked_times = Appointment.objects.filter(
            doctor=doctor,
            date=date,
            status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
        ).values_list('time', flat=True)

        booked_times_set = set(booked_times)
        available = [slot for slot in all_slots if slot not in booked_times_set]

        return Response({
            'doctor':          doctor.full_name,
            'date':            str(date),
            'slot_duration':   schedule.slot_duration_minutes,
            'available_slots': [t.strftime('%H:%M') for t in available],
        })

    def _generate_slots(self, start, end, duration_minutes):
        slots   = []
        current = datetime.datetime.combine(datetime.date.today(), start)
        end_dt  = datetime.datetime.combine(datetime.date.today(), end)
        delta   = datetime.timedelta(minutes=duration_minutes)
        while current < end_dt:
            slots.append(current.time())
            current += delta
        return slots
