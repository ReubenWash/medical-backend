from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PatientProfile, EmailVerificationToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ('email', 'full_name', 'role', 'gender', 'is_email_verified', 'is_active', 'date_joined')
    list_filter   = ('role', 'is_active', 'is_email_verified', 'gender')
    search_fields = ('email', 'first_name', 'last_name')
    ordering      = ('-date_joined',)

    fieldsets = (
        (None,           {'fields': ('email', 'password')}),
        ('Personal',     {'fields': ('first_name', 'last_name', 'phone', 'gender')}),
        ('Permissions',  {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'is_email_verified', 'groups', 'user_permissions')}),
        ('Dates',        {'fields': ('date_joined', 'last_login')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields':  ('email', 'first_name', 'last_name', 'phone', 'gender', 'role', 'password1', 'password2'),
        }),
    )
    readonly_fields = ('date_joined', 'last_login')


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'gender', 'blood_group', 'date_of_birth')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display  = ('user', 'token', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('token', 'created_at')
