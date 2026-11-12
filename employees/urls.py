from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

from employees.views import (
    dashboard_view, 
    employee_list_view, 
    employee_create_view, 
    employee_update_view,
    employee_detail_view,
    absence_list_view,
    absence_create_view,
    absence_detail_view,
    absence_update_view,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_view, name='dashboard'),
    path('employees/', employee_list_view, name='employee_list'),
    path('employees/nuevo/', employee_create_view, name='employee_create'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('absences/', views.absence_list_view, name='absence_list'),
    path('absences/create/', views.absence_create_view, name='absence_create'),
    path('export/employees/', views.export_employees_csv, name='export_employees_csv'),
    path('import/employees/', views.import_employees_csv, name='import_employees_csv'),
    path('import/employees/template/', views.download_employee_template, name='download_employee_template'),

    # RUTAS DINÁMICAS 
    path('employees/editar/<int:pk>/', employee_update_view, name='employee_update'),
    path('employee/<int:pk>/', employee_detail_view, name='employee_detail'),
    path('absences/<int:pk>/', views.absence_detail_view, name='absence_detail'),
    path('absences/<int:pk>/editar/', views.absence_update_view, name='absence_update'),
]