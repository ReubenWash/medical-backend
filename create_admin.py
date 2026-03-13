import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicare_backend.settings')
django.setup()

from accounts.models import User

email    = 'admin@clinic.com'
password = 'Admin1234!'

if not User.objects.filter(email=email).exists():
    u = User.objects.create_superuser(
        email=email,
        password=password,
        first_name='Admin',
        last_name='User',
    )
    u.role = 'admin'
    u.is_email_verified = True
    u.save()
    print(f'Admin created: {email}')
else:
    print('Admin already exists.')
