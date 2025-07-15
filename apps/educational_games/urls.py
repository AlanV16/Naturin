from django.urls import path
from . import views

app_name = 'educational_games'

urlpatterns = [
    # ============================================================================
    # DASHBOARD Y GESTIÓN PRINCIPAL
    # ============================================================================
    path('dashboard/', views.activity_dashboard, name='activity_dashboard'),
    
    # ============================================================================
    # TAREAS
    # ============================================================================
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/create/', views.assignment_create, name='assignment_create'),
    path('assignments/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('assignments/<int:assignment_id>/edit/', views.assignment_edit, name='assignment_edit'),
    path('assignments/<int:assignment_id>/submissions/', views.assignment_submissions, name='assignment_submissions'),
    path('submissions/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
    
    # ============================================================================
    # LECTURAS
    # ============================================================================
    path('readings/', views.reading_list, name='reading_list'),
    path('readings/create/', views.reading_create, name='reading_create'),
    path('readings/<int:reading_id>/', views.reading_detail, name='reading_detail'),
    
    # ============================================================================
    # TESTS
    # ============================================================================
    path('tests/', views.test_list, name='test_list'),
    path('tests/create/', views.test_create, name='test_create'),
    path('tests/<int:test_id>/', views.test_detail, name='test_detail'),
    path('tests/<int:test_id>/edit/', views.test_edit, name='test_edit'),
    path('tests/<int:test_id>/take/', views.test_take, name='test_take'),
    path('tests/<int:test_id>/results/', views.test_results, name='test_results'),
    
    # ============================================================================
    # JUEGOS
    # ============================================================================
    path('games/', views.game_list, name='game_list'),
    path('games/create/', views.game_create, name='game_create'),
    path('games/<int:game_id>/', views.game_detail, name='game_detail'),
    
    # ============================================================================
    # ASIGNACIÓN A CLASES
    # ============================================================================
    path('assign/<str:activity_type>/<int:activity_id>/', views.assign_activity_to_classroom, name='assign_activity'),
    
    # ============================================================================
    # VISTAS DE ESTUDIANTES
    # ============================================================================
    path('student/assignments/', views.student_assignments, name='student_assignments'),
    path('student/assignments/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),

    # ============================================================================
    # API ENDPOINTS
    # ============================================================================
    path('api/assignment/create/', views.assignment_create_api, name='assignment_create_api'),
    path('api/assignment/edit/<int:assignment_id>/', views.assignment_edit_api, name='assignment_edit_api'),
    path('api/assignment/delete/<int:assignment_id>/', views.assignment_delete_api, name='assignment_delete_api'),
    path('api/assignment/assign_classes/<int:assignment_id>/', views.assignment_assign_classes_api, name='assignment_assign_classes_api'),
    path('api/assignment/public_list/', views.assignment_public_list_api, name='assignment_public_list_api'),
] 
 
 