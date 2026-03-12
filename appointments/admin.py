from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display   = ('id', 'patient', 'doctor', 'date', 'time', 'appointment_type', 'status')
    list_filter    = ('status', 'appointment_type', 'date')
    search_fields  = ('patient__email', 'patient__first_name', 'doctor__first_name', 'doctor__last_name')
    ordering       = ('-date', '-time')
    date_hierarchy = 'date'