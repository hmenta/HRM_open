from django.contrib import admin
from django.urls import path
from employees.views import (
    dashboard_view, 
    employee_list_view, 
    employee_create_view, 
    employee_update_view
)
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_view, name='dashboard'),
    path('employees/', employee_list_view, name='employee_list'),
    path('employees/nuevo/', employee_create_view, name='employee_create'),
    path('employees/editar/<int:pk>/', employee_update_view, name='employee_update'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
]