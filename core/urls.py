from django.urls import path

from . import api_views, views

urlpatterns = [
    path('settings/', views.settings_hub_view, name='settings_hub'),
    path('settings/email/', views.settings_email_view, name='settings_email'),
    path('settings/email/test/', views.settings_email_test_view, name='settings_email_test'),
    path('settings/api/', views.settings_api_view, name='settings_api'),
    path('settings/api/<int:pk>/toggle/', views.settings_api_toggle_view, name='settings_api_toggle'),
    path('settings/api/<int:pk>/eliminar/', views.settings_api_delete_view, name='settings_api_delete'),
    path('settings/notifications/', views.settings_notifications_view, name='settings_notifications'),

    # API v1 — recibos
    path('api/v1/health/', api_views.api_health, name='api_health'),
    path('api/v1/payslips/', api_views.api_payslip_upload, name='api_payslip_upload'),
    path('api/v1/payslips/bulk/', api_views.api_payslip_bulk_upload, name='api_payslip_bulk'),
]
