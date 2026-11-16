from django.urls import path
from . import views

app_name = 'recruitment'

urlpatterns = [
    # Kanban y Actualizaciones AJAX
    path('', views.kanban_board_view, name='kanban_board'),
    path('applications/<int:pk>/update-stage-ajax/', views.update_stage_ajax, name='update_stage_ajax'),
    path('applications/<int:pk>/move/', views.application_move, name='application_move'),

    # Búsquedas (Positions)
    path('positions/', views.position_list, name='position_list'),
    path('positions/create/', views.position_create, name='position_create'),
    path('positions/<int:pk>/', views.position_detail, name='position_detail'),
    path('positions/<int:pk>/edit/', views.position_edit, name='position_edit'),

    # Postulantes (Candidates)
    path('candidates/', views.candidate_list, name='candidate_list'),
    path('candidates/create/', views.candidate_create, name='candidate_create'),
    path('candidates/<int:pk>/', views.candidate_detail, name='candidate_detail'),
    path('candidates/<int:pk>/edit/', views.candidate_edit, name='candidate_edit'),
    path('candidates/<int:pk>/cv/', views.candidate_cv, name='candidate_cv'),
    path('candidates/<int:pk>/assign/', views.assign_candidate_position, name='assign_candidate_position'),

    # Portal de Empleo
    path('portal/apply/', views.portal_apply, name='portal_apply'),
    path('portal/thanks/', views.portal_thanks, name='portal_thanks'),
]
