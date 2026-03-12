from django.db.models.signals import post_save
from django.dispatch import receiver
from appointments.models import Appointment
from .models import Payment


@receiver(post_save, sender=Appointment)
def create_payment_on_confirm(sender, instance, **kwargs):
    if instance.status == Appointment.Status.CONFIRMED:
        Payment.objects.get_or_create(
            appointment=instance,
            defaults={
                'amount': instance.doctor.consultation_fee,
                'status': Payment.Status.PENDING,
            }
        )