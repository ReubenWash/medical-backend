from rest_framework import serializers
from .models import Payment
from appointments.serializers import AppointmentSerializer


class PaymentSerializer(serializers.ModelSerializer):
    appointment    = AppointmentSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    method_display = serializers.CharField(source='get_method_display', read_only=True)

    class Meta:
        model  = Payment
        fields = [
            'id', 'invoice_number', 'appointment',
            'amount', 'status', 'status_display',
            'method', 'method_display', 'transaction_ref',
            'notes', 'paid_at', 'refunded_at', 'created_at',
        ]
        read_only_fields = ['invoice_number', 'created_at', 'paid_at', 'refunded_at']


class PaymentUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model  = Payment
        fields = ['status', 'method', 'transaction_ref', 'notes', 'amount']

    def update(self, instance, validated_data):
        from django.utils import timezone
        new_status = validated_data.get('status', instance.status)

        if new_status == Payment.Status.PAID and instance.status != Payment.Status.PAID:
            instance.paid_at = timezone.now()
        elif new_status == Payment.Status.REFUNDED:
            instance.refunded_at = timezone.now()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance