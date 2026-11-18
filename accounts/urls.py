from django.urls import path

from . import views

urlpatterns = [
    path('users/', views.user_list_view, name='user_list'),
    path('users/nuevo/', views.user_create_view, name='user_create'),
    path('users/editar/<int:pk>/', views.user_update_view, name='user_update'),
    path('users/<int:pk>/toggle-activo/', views.user_toggle_active_view, name='user_toggle_active'),
]
