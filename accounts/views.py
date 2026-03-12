from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils import timezone

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import PatientProfile, EmailVerificationToken
from .serializers import (
    MyTokenObtainPairSerializer,
    RegisterSerializer,
    UserSerializer,
    UpdateProfileSerializer,
    ChangePasswordSerializer,
    PatientProfileSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from .permissions import IsAdminUser, IsOwnerOrAdmin

User = get_user_model()


# ── Auth ───────────────────────────────────────────────────────────────────────

class LoginView(TokenObtainPairView):
    serializer_class   = MyTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


class RegisterView(generics.CreateAPIView):
    serializer_class   = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send email verification
        _send_verification_email(user)

        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Account created successfully. Please check your email to verify your account.',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access':  str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)
        except TokenError:
            # Already blacklisted or invalid — still treat as logged out
            return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Could not logout. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)


# ── Email Verification ─────────────────────────────────────────────────────────

class VerifyEmailView(APIView):
    """GET /api/v1/auth/verify-email/?token=<uuid>"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        token_value = request.query_params.get('token')
        if not token_value:
            return Response({'error': 'Verification token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token_obj = EmailVerificationToken.objects.get(token=token_value)
        except EmailVerificationToken.DoesNotExist:
            return Response({'error': 'Invalid or expired verification link.'}, status=status.HTTP_400_BAD_REQUEST)

        if token_obj.is_expired():
            token_obj.delete()
            return Response({'error': 'Verification link has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

        user = token_obj.user
        user.is_email_verified = True
        user.save()
        token_obj.delete()

        return Response({'message': 'Email verified successfully! You can now log in.'}, status=status.HTTP_200_OK)


class ResendVerificationEmailView(APIView):
    """POST /api/v1/auth/resend-verification/  body: { "email": "..." }"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'message': 'If that email is registered, a verification link has been sent.'})

        if user.is_email_verified:
            return Response({'message': 'Email is already verified.'})

        _send_verification_email(user)
        return Response({'message': 'Verification email sent. Please check your inbox.'})


# ── Password Reset ─────────────────────────────────────────────────────────────

class ForgotPasswordView(APIView):
    """POST /api/v1/auth/forgot-password/  body: { "email": "..." }"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email, is_active=True)
            _send_password_reset_email(user)
        except User.DoesNotExist:
            pass  # Don't reveal whether email exists

        return Response({
            'message': 'If an account with that email exists, a password reset link has been sent.'
        })


class ResetPasswordView(APIView):
    """POST /api/v1/auth/reset-password/
    body: { "uid": "...", "token": "...", "new_password": "...", "new_password2": "..." }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            uid  = force_str(urlsafe_base64_decode(serializer.validated_data['uid']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'error': 'Invalid reset link.'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, serializer.validated_data['token']):
            return Response({'error': 'Reset link is invalid or has expired.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Password reset successfully. You can now log in with your new password.'})


# ── Profile ────────────────────────────────────────────────────────────────────

class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UpdateProfileSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'message': 'Password changed successfully.'})


# ── Admin: Users ───────────────────────────────────────────────────────────────

class UserListView(generics.ListAPIView):
    serializer_class   = UserSerializer
    permission_classes = [IsAdminUser]
    filterset_fields   = ['role', 'is_active']
    search_fields      = ['email', 'first_name', 'last_name', 'phone']
    ordering_fields    = ['date_joined', 'first_name']

    def get_queryset(self):
        return User.objects.select_related('patient_profile').all()


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = UserSerializer
    permission_classes = [IsAdminUser]
    queryset           = User.objects.select_related('patient_profile').all()

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'message': f'User {user.email} deactivated.'}, status=status.HTTP_200_OK)


class AdminResetUserPasswordView(APIView):
    """POST /api/v1/auth/users/<pk>/reset-password/
    Admin triggers a password reset email for any user.
    """
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk, is_active=True)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        _send_password_reset_email(user)
        return Response({'message': f'Password reset email sent to {user.email}.'})


class AdminDashboardStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        from appointments.models import Appointment
        from payments.models import Payment
        from django.db.models import Sum

        today = timezone.now().date()

        total_patients      = User.objects.filter(role=User.Role.PATIENT, is_active=True).count()
        todays_appointments = Appointment.objects.filter(date=today).count()
        upcoming            = Appointment.objects.filter(
            date__gt=today, status=Appointment.Status.CONFIRMED
        ).count()
        monthly_revenue = Payment.objects.filter(
            status=Payment.Status.PAID,
            paid_at__year=today.year,
            paid_at__month=today.month,
        ).aggregate(total=Sum('amount'))['total'] or 0

        return Response({
            'total_patients':        total_patients,
            'todays_appointments':   todays_appointments,
            'upcoming_appointments': upcoming,
            'monthly_revenue':       monthly_revenue,
        })


# ── Helpers ────────────────────────────────────────────────────────────────────

def _send_verification_email(user):
    """Create an email verification token and send the link to the user."""
    EmailVerificationToken.objects.filter(user=user).delete()
    token_obj    = EmailVerificationToken.objects.create(user=user)
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
    verify_url   = f"{frontend_url}/verify-email?token={token_obj.token}"

    send_mail(
        subject='Verify your MediCare email address',
        message=(
            f"Hi {user.first_name},\n\n"
            f"Thank you for registering with MediCare Clinic.\n\n"
            f"Please verify your email by clicking the link below:\n\n"
            f"{verify_url}\n\n"
            f"This link expires in 24 hours.\n\n"
            f"If you did not create this account, please ignore this email.\n\n"
            f"— The MediCare Team"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def _send_password_reset_email(user):
    """Generate a Django password-reset token and email the reset link."""
    uid          = urlsafe_base64_encode(force_bytes(user.pk))
    token        = default_token_generator.make_token(user)
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
    reset_url    = f"{frontend_url}/reset-password?uid={uid}&token={token}"

    send_mail(
        subject='Reset your MediCare password',
        message=(
            f"Hi {user.first_name},\n\n"
            f"We received a request to reset your MediCare Clinic password.\n\n"
            f"Click the link below to set a new password:\n\n"
            f"{reset_url}\n\n"
            f"This link expires in 1 hour.\n\n"
            f"If you did not request this, please ignore this email.\n\n"
            f"— The MediCare Team"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )
