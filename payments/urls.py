from django.urls import path
from .views import PaymentListView, PaymentDetailView, PaymentAdminUpdateView, RevenueReportView

urlpatterns = [
    path('',               PaymentListView.as_view(),        name='payment-list'),
    path('<int:pk>/',       PaymentDetailView.as_view(),      name='payment-detail'),
    path('<int:pk>/manage/', PaymentAdminUpdateView.as_view(), name='payment-manage'),
    path('revenue/',        RevenueReportView.as_view(),      name='revenue-report'),
]