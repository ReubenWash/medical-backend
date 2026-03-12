from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display    = ('invoice_number', 'appointment', 'amount', 'method', 'status', 'paid_at')
    list_filter     = ('status', 'method')
    search_fields   = ('invoice_number', 'appointment__patient__email', 'appointment__patient__first_name')
    ordering        = ('-created_at',)
    readonly_fields = ('invoice_number', 'paid_at', 'refunded_at', 'created_at', 'updated_at')