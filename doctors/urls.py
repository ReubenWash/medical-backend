from django.urls import path
from .views import (
    DoctorListCreateView,
    DoctorDetailView,
    DoctorPhotoUploadView,
    DoctorScheduleView,
    DoctorScheduleDetailView,
    DoctorAvailableSlotsView,
)

urlpatterns = [
    path('',                                     DoctorListCreateView.as_view(),    name='doctor-list'),
    path('<int:pk>/',                            DoctorDetailView.as_view(),         name='doctor-detail'),
    path('<int:pk>/photo/',                      DoctorPhotoUploadView.as_view(),    name='doctor-photo'),
    path('<int:pk>/schedule/',                   DoctorScheduleView.as_view(),       name='doctor-schedule'),
    path('<int:pk>/schedule/<int:schedule_id>/', DoctorScheduleDetailView.as_view(), name='doctor-schedule-detail'),
    path('<int:pk>/available-slots/',            DoctorAvailableSlotsView.as_view(), name='doctor-slots'),
]
