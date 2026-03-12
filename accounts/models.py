import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        extra_fields.setdefault('is_email_verified', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        PATIENT = 'patient', 'Patient'
        ADMIN   = 'admin',   'Admin'
        DOCTOR  = 'doctor',  'Doctor'

    class Gender(models.TextChoices):
        MALE       = 'male',       'Male'
        FEMALE     = 'female',     'Female'
        OTHER      = 'other',      'Other'
        PREFER_NOT = 'prefer_not', 'Prefer not to say'

    email      = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name  = models.CharField(max_length=150)
    phone      = models.CharField(max_length=20, blank=True)
    gender     = models.CharField(max_length=15, choices=Gender.choices, blank=True)
    role       = models.CharField(max_length=10, choices=Role.choices, default=Role.PATIENT)

    is_active         = models.BooleanField(default=True)
    is_staff          = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.full_name} ({self.email})'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN


class PatientProfile(models.Model):

    class Gender(models.TextChoices):
        MALE       = 'male',       'Male'
        FEMALE     = 'female',     'Female'
        OTHER      = 'other',      'Other'
        PREFER_NOT = 'prefer_not', 'Prefer not to say'

    class BloodGroup(models.TextChoices):
        A_POS  = 'A+',  'A+'
        A_NEG  = 'A-',  'A-'
        B_POS  = 'B+',  'B+'
        B_NEG  = 'B-',  'B-'
        AB_POS = 'AB+', 'AB+'
        AB_NEG = 'AB-', 'AB-'
        O_POS  = 'O+',  'O+'
        O_NEG  = 'O-',  'O-'

    user              = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth     = models.DateField(null=True, blank=True)
    gender            = models.CharField(max_length=15, choices=Gender.choices, blank=True)
    blood_group       = models.CharField(max_length=5, choices=BloodGroup.choices, blank=True)
    address           = models.TextField(blank=True)
    emergency_contact_name  = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    allergies         = models.TextField(blank=True)
    medical_history   = models.TextField(blank=True)
    profile_picture   = models.ImageField(upload_to='patients/profiles/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile of {self.user.full_name}'

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = timezone.now().date()
        dob   = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


class EmailVerificationToken(models.Model):
    """One-time token used to verify a user's email address."""
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification_token')
    token      = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        """Token expires after 24 hours."""
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(hours=24)

    def __str__(self):
        return f'VerificationToken for {self.user.email}'
