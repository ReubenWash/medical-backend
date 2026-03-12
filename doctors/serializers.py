from rest_framework import serializers
from .models import Doctor, DoctorSchedule


class DoctorScheduleSerializer(serializers.ModelSerializer):
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model  = DoctorSchedule
        fields = [
            'id', 'day_of_week', 'day_of_week_display',
            'start_time', 'end_time', 'slot_duration_minutes', 'is_available',
        ]


class DoctorSerializer(serializers.ModelSerializer):
    schedules      = DoctorScheduleSerializer(many=True, read_only=True)
    full_name      = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    # Returns the full absolute URL (e.g. https://res.cloudinary.com/... or http://localhost/media/...)
    photo_url      = serializers.SerializerMethodField()

    class Meta:
        model  = Doctor
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'specialty',
            'email', 'phone', 'bio', 'photo', 'photo_url', 'status', 'status_display',
            'consultation_fee', 'schedules', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_photo_url(self, obj):
        if not obj.photo:
            return None
        request = self.context.get('request')
        # Cloudinary URLs are already absolute; local ones need the request for the host
        url = obj.photo.url
        if url.startswith('http'):
            return url
        if request:
            return request.build_absolute_uri(url)
        return url


class DoctorWriteSerializer(serializers.ModelSerializer):
    """Used for POST (create) and PATCH/PUT (update) — admin only."""
    photo_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = Doctor
        fields = [
            'first_name', 'last_name', 'specialty', 'email', 'phone',
            'bio', 'photo', 'photo_url', 'status', 'consultation_fee',
        ]
        extra_kwargs = {
            'photo': {
                'required': False,
                'allow_null': True,
                # Accepts multipart/form-data uploads
                'use_url': True,
            }
        }

    def get_photo_url(self, obj):
        if not obj.photo:
            return None
        request = self.context.get('request')
        url = obj.photo.url
        if url.startswith('http'):
            return url
        if request:
            return request.build_absolute_uri(url)
        return url


class DoctorPhotoUploadSerializer(serializers.ModelSerializer):
    """Dedicated serializer for PATCH /api/v1/doctors/<pk>/photo/ endpoint."""
    photo_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = Doctor
        fields = ['photo', 'photo_url']
        extra_kwargs = {
            'photo': {'required': True}
        }

    def get_photo_url(self, obj):
        if not obj.photo:
            return None
        request = self.context.get('request')
        url = obj.photo.url
        if url.startswith('http'):
            return url
        if request:
            return request.build_absolute_uri(url)
        return url


class AvailableSlotsSerializer(serializers.Serializer):
    date = serializers.DateField(required=True)
