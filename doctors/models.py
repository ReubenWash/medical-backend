from django.db import models


class Doctor(models.Model):

    class Status(models.TextChoices):
        ACTIVE   = 'active',   'Active'
        INACTIVE = 'inactive', 'Inactive'
        ON_LEAVE = 'on_leave', 'On Leave'

    first_name       = models.CharField(max_length=100)
    last_name        = models.CharField(max_length=100)
    specialty        = models.CharField(max_length=150)
    email            = models.EmailField(unique=True)
    phone            = models.CharField(max_length=20)
    bio              = models.TextField(blank=True)
    photo            = models.ImageField(upload_to='doctors/photos/', null=True, blank=True)
    status           = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'Dr. {self.first_name} {self.last_name} — {self.specialty}'

    @property
    def full_name(self):
        return f'Dr. {self.first_name} {self.last_name}'


class DoctorSchedule(models.Model):

    class DayOfWeek(models.IntegerChoices):
        MONDAY    = 0, 'Monday'
        TUESDAY   = 1, 'Tuesday'
        WEDNESDAY = 2, 'Wednesday'
        THURSDAY  = 3, 'Thursday'
        FRIDAY    = 4, 'Friday'
        SATURDAY  = 5, 'Saturday'
        SUNDAY    = 6, 'Sunday'

    doctor                = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules')
    day_of_week           = models.IntegerField(choices=DayOfWeek.choices)
    start_time            = models.TimeField()
    end_time              = models.TimeField()
    slot_duration_minutes = models.PositiveIntegerField(default=30)
    is_available          = models.BooleanField(default=True)

    class Meta:
        unique_together = ('doctor', 'day_of_week')
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f'{self.doctor.full_name} — {self.get_day_of_week_display()} {self.start_time}–{self.end_time}'