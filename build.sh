#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
echo "from accounts.models import User; User.objects.filter(email='admin@clinic.com').exists() or User.objects.create_superuser(email='admin@clinic.com', password='Admin1234!')" | python manage.py shell