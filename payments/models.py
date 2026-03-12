import uuid
from django.db import models
from appointments.models import Appointment


def generate_invoice_number():
    return f'INV-{uuid.uuid4().hex[:8].upper()}'


class Payment(models.Model):

    class Status(models.TextChoices):
        PENDING  = 'pending',  'Pending'
        PAID     = 'paid',     'Paid'
        REFUNDED = 'refunded', 'Refunded'
        FAILED   = 'failed',   'Failed'

    class Method(models.TextChoices):
        CASH         = 'cash',         'Cash'
        CARD         = 'card',         'Credit/Debit Card'
        MOBILE_MONEY = 'mobile_money', 'Mobile Money'
        INSURANCE    = 'insurance',    'Insurance'
        BANK         = 'bank',         'Bank Transfer'

    appointment     = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='payment')
    invoice_number  = models.CharField(max_length=20, unique=True, default=generate_invoice_number)
    amount          = models.DecimalField(max_digits=10, decimal_places=2)
    status          = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    method          = models.CharField(max_length=15, choices=Method.choices, blank=True)
    transaction_ref = models.CharField(max_length=100, blank=True)
    notes           = models.TextField(blank=True)

    paid_at     = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.invoice_number} — {self.appointment.patient.full_name} — {self.get_status_display()}'