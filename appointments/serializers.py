from django.utils import timezone
from rest_framework import serializers

from accounts.serializers import UserSerializer
from doctors.serializers import DoctorSerializer
from .models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    patient        = UserSerializer(read_only=True)
    doctor         = DoctorSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display   = serializers.CharField(source='get_appointment_type_display', read_only=True)

    class Meta:
        model  = Appointment
        fields = [
            'id', 'patient', 'doctor',
            'date', 'time', 'appointment_type', 'type_display',
            'status', 'status_display', 'reason',
            'confirmed_at', 'cancelled_at', 'completed_at',
            'cancellation_reason', 'created_at', 'updated_at',
        ]
        read_only_fields = ['confirmed_at', 'cancelled_at', 'completed_at', 'created_at', 'updated_at']


class AppointmentCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model  = Appointment
        fields = ['doctor', 'date', 'time', 'appointment_type', 'reason']

    def validate_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError('Appointment date cannot be in the past.')
        return value

    def validate(self, attrs):
        doctor = attrs.get('doctor')
        date   = attrs.get('date')
        time   = attrs.get('time')

        if Appointment.objects.filter(
            doctor=doctor, date=date, time=time,
            status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
        ).exists():
            raise serializers.ValidationError('This time slot is already booked. Please choose another.')

        day_of_week = date.weekday()
        if not doctor.schedules.filter(day_of_week=day_of_week, is_available=True).exists():
            raise serializers.ValidationError('The doctor is not available on the selected date.')

        return attrs

    def create(self, validated_data):
        return Appointment.objects.create(**validated_data)


class AppointmentAdminUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model  = Appointment
        fields = ['status', 'admin_notes', 'cancellation_reason', 'time', 'date']

    def validate_status(self, value):
        instance = self.instance
        if instance:
            if instance.status in [Appointment.Status.COMPLETED, Appointment.Status.CANCELLED]:
                raise serializers.ValidationError(
                    f'Cannot change status of a {instance.get_status_display()} appointment.'
                )
        return value

    def update(self, instance, validated_data):
        new_status = validated_data.get('status', instance.status)
        now = timezone.now()

        if new_status == Appointment.Status.CONFIRMED and instance.status == Appointment.Status.PENDING:
            instance.confirmed_at = now
        elif new_status == Appointment.Status.CANCELLED:
            instance.cancelled_at = now
            instance.cancelled_by = self.context['request'].user
        elif new_status == Appointment.Status.COMPLETED:
            instance.completed_at = now

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class CancelAppointmentSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)