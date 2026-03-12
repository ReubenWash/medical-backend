from django.contrib import admin
from django.utils.html import format_html
from .models import Doctor, DoctorSchedule


class DoctorScheduleInline(admin.TabularInline):
    model  = DoctorSchedule
    extra  = 0
    fields = ('day_of_week', 'start_time', 'end_time', 'slot_duration_minutes', 'is_available')


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display  = ('photo_thumbnail', 'full_name', 'specialty', 'email', 'status', 'consultation_fee')
    list_filter   = ('status', 'specialty')
    search_fields = ('first_name', 'last_name', 'email', 'specialty')
    ordering      = ('last_name', 'first_name')
    inlines       = [DoctorScheduleInline]
    readonly_fields = ('photo_thumbnail', 'created_at', 'updated_at')

    fieldsets = (
        ('Personal',     {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('Professional', {'fields': ('specialty', 'bio', 'consultation_fee', 'status')}),
        ('Photo',        {'fields': ('photo', 'photo_thumbnail')}),
        ('Timestamps',   {'fields': ('created_at', 'updated_at')}),
    )

    def photo_thumbnail(self, obj):
        if obj.photo:
            try:
                url = obj.photo.url
                return format_html(
                    '<img src="{}" style="width:50px;height:50px;object-fit:cover;border-radius:50%;" />',
                    url
                )
            except Exception:
                return '—'
        return '—'
    photo_thumbnail.short_description = 'Photo'


@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display  = ('doctor', 'get_day_of_week_display', 'start_time', 'end_time', 'is_available')
    list_filter   = ('day_of_week', 'is_available')
    search_fields = ('doctor__first_name', 'doctor__last_name')
