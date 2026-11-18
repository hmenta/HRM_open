from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from employees.views import (
    dashboard_view,
    employee_list_view,
    employee_create_view,
    employee_update_view,
    employee_detail_view,
)
from recruitment.views import portal_apply, portal_thanks

from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Autenticación
    path('accounts/login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('', dashboard_view, name='dashboard'),
    path('employees/', employee_list_view, name='employee_list'),
    path('employees/nuevo/', employee_create_view, name='employee_create'),
    path('employees/editar/<int:pk>/', employee_update_view, name='employee_update'),
    path('employees/ver/<int:pk>/', employee_detail_view, name='employee_detail'),
    path('recruitment/', include('recruitment.urls')),

    # Portal público de candidatos (frontend separado del HRM)
    path('empleo/', portal_apply, name='empleo_apply'),
    path('empleo/gracias/', portal_thanks, name='empleo_thanks'),

    path('', include('accounts.urls')),
    path('', include('core.urls')),
    path('', include('employees.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
