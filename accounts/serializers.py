from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import PatientProfile

User = get_user_model()


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['full_name']         = user.full_name
        token['email']             = user.email
        token['role']              = user.role
        token['is_email_verified'] = user.is_email_verified
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id':               self.user.id,
            'email':            self.user.email,
            'full_name':        self.user.full_name,
            'role':             self.user.role,
            'phone':            self.user.phone,
            'gender':           self.user.gender,
            'is_email_verified': self.user.is_email_verified,
        }
        return data


class PatientProfileSerializer(serializers.ModelSerializer):
    age = serializers.ReadOnlyField()

    class Meta:
        model  = PatientProfile
        fields = [
            'id', 'date_of_birth', 'gender', 'blood_group',
            'address', 'emergency_contact_name', 'emergency_contact_phone',
            'allergies', 'medical_history', 'profile_picture', 'age',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    patient_profile = PatientProfileSerializer(read_only=True)
    full_name = serializers.ReadOnlyField()

    class Meta:
        model  = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone', 'gender',
            'role', 'full_name', 'is_active', 'is_email_verified',
            'date_joined', 'patient_profile',
        ]
        read_only_fields = ['date_joined', 'role', 'is_email_verified']


class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label='Confirm Password')

    class Meta:
        model  = User
        # gender is optional at signup
        fields = ['email', 'first_name', 'last_name', 'phone', 'gender', 'password', 'password2']
        extra_kwargs = {
            'gender': {'required': False, 'allow_blank': True},
            'phone':  {'required': False, 'allow_blank': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            role=User.Role.PATIENT,
            **validated_data,
        )
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value


class UpdateProfileSerializer(serializers.ModelSerializer):
    patient_profile = PatientProfileSerializer(required=False)

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'phone', 'gender', 'patient_profile']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('patient_profile', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if profile_data:
            profile = instance.patient_profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance


# ── Password Reset Serializers ─────────────────────────────────────────────────

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid           = serializers.CharField(required=True)
    token         = serializers.CharField(required=True)
    new_password  = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True, write_only=True, label='Confirm new password')

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password': 'Passwords do not match.'})
        return attrs


class AdminPasswordResetSerializer(serializers.Serializer):
    """Used by admin to trigger a password reset email for a specific user."""
    user_id = serializers.IntegerField(required=True)
