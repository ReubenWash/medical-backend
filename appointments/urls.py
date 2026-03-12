from django.urls import path
from .views import (
    AppointmentListCreateView,
    AppointmentDetailView,
    AppointmentAdminUpdateView,
    CancelAppointmentView,
    TodaysAppointmentsView,
    AppointmentCalendarView,
)

urlpatterns = [
    path('',                 AppointmentListCreateView.as_view(),  name='appointment-list'),
    path('<int:pk>/',         AppointmentDetailView.as_view(),      name='appointment-detail'),
    path('<int:pk>/manage/',  AppointmentAdminUpdateView.as_view(), name='appointment-manage'),
    path('<int:pk>/cancel/',  CancelAppointmentView.as_view(),      name='appointment-cancel'),
    path('today/',            TodaysAppointmentsView.as_view(),     name='appointments-today'),
    path('calendar/',         AppointmentCalendarView.as_view(),    name='appointments-calendar'),
]