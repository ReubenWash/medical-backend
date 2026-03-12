from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Appointment(models.Model):

    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        NO_SHOW   = 'no_show',   'No Show'

    class AppointmentType(models.TextChoices):
        GENERAL    = 'general',    'General Consultation'
        FOLLOW_UP  = 'follow_up',  'Follow-Up'
        SPECIALIST = 'specialist', 'Specialist'
        EMERGENCY  = 'emergency',  'Emergency'
        CHECKUP    = 'checkup',    'Routine Check-up'

    patient          = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='appointments',
        limit_choices_to={'role': 'patient'},
    )
    doctor           = models.ForeignKey(
        'doctors.Doctor', on_delete=models.CASCADE, related_name='appointments',
    )
    date             = models.DateField()
    time             = models.TimeField()
    appointment_type = models.CharField(max_length=15, choices=AppointmentType.choices, default=AppointmentType.GENERAL)
    status           = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    reason           = models.TextField(blank=True)
    admin_notes      = models.TextField