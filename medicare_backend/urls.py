from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/v1/auth/',         include('accounts.urls')),
    path('api/v1/doctors/',      include('doctors.urls')),
    path('api/v1/appointments/', include('appointments.urls')),
    path('api/v1/payments/',     include('payments.urls')),
]

# Serve media files locally when Cloudinary is not configured
# (In production with Cloudinary, files are served directly from Cloudinary CDN)
if not getattr(settings, 'CLOUDINARY_URL', ''):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
