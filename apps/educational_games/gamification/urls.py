from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    # ============================================================================
    # VISTAS PRINCIPALES
    # ============================================================================
    path('', views.dashboard, name='dashboard'),
    path('games/', views.game_list, name='game_list'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('leaderboard/<int:game_id>/', views.leaderboard, name='game_leaderboard'),
    
    # ============================================================================
    # GESTIÓN DE AULAS (DOCENTES)
    # ============================================================================
    path('aulas/', views.aula_list, name='aula_list'),
    path('aulas/crear/', views.aula_create, name='aula_create'),
    path('aulas/<int:aula_id>/', views.aula_detail, name='aula_detail'),
    
    # ============================================================================
    # GESTIÓN DE ACTIVIDADES
    # ============================================================================
    path('aulas/<int:aula_id>/actividad/crear/', views.actividad_create, name='actividad_create'),
    path('actividades/<int:actividad_id>/', views.actividad_detail, name='actividad_detail'),
    
    # ============================================================================
    # DESAFÍOS
    # ============================================================================
    path('desafios/', views.desafios_list, name='desafios_list'),
    path('desafios/<int:desafio_id>/', views.desafio_detail, name='desafio_detail'),
    
    # ============================================================================
    # RANKINGS Y ESTADÍSTICAS
    # ============================================================================
    path('rankings/', views.rankings_list, name='rankings_list'),
    path('estadisticas/', views.estadisticas_personales, name='estadisticas_personales'),
    
    # ============================================================================
    # GESTIÓN DE JUEGOS
    # ============================================================================
    path('games/crear/', views.game_create, name='game_create'),
    path('games/editar/<int:game_id>/', views.game_edit, name='game_edit'),
    
    # ============================================================================
    # JUGAR JUEGOS
    # ============================================================================
    path('games/quiz/<int:game_id>/', views.quiz_play, name='quiz_play'),
    path('games/rapid-questions/<int:game_id>/', views.rapid_questions_play, name='rapid_questions_play'),
    
    # ============================================================================
    # PERFILES DE USUARIO
    # ============================================================================
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/<str:username>/', views.user_profile, name='user_profile_detail'),
    
    # ============================================================================
    # APIs PARA JUEGOS
    # ============================================================================
    path('api/questions/<int:game_id>/', views.api_question_data, name='api_question_data'),
    path('api/submit/<int:session_id>/', views.api_submit_answer, name='api_submit_answer'),
    
    # ============================================================================
    # NOTIFICACIONES
    # ============================================================================
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/count/', views.notifications_count, name='notifications_count'),
    path('notifications/ajax/', views.notifications_ajax, name='notifications_ajax'),

    # ============================================================================
    # TESTS Y CUESTIONARIOS
    # ============================================================================
    path('aulas/<int:aula_id>/tests/', views.test_list, name='test_list'),
    path('aulas/<int:aula_id>/tests/crear/', views.test_create, name='test_create'),
    path('tests/<int:test_id>/', views.test_detail, name='test_detail'),
    path('tests/<int:test_id>/editar/', views.test_edit, name='test_edit'),
    path('tests/<int:test_id>/eliminar/', views.test_delete, name='test_delete'),
    path('tests/<int:test_id>/pregunta/crear/', views.pregunta_create, name='pregunta_create'),
    path('tests/<int:test_id>/tomar/', views.test_take, name='test_take'),
    path('tests/<int:test_id>/resultados/', views.test_results, name='test_results'),
    path('tests/<int:test_id>/resultados/exportar/', views.test_export_results, name='test_export_results'),
    path('tests/<int:test_id>/duplicar/', views.test_duplicate, name='test_duplicate'),
    path('resultados/<int:resultado_id>/', views.test_results_detail, name='test_results_detail'),
    
    # ============================================================================
    # TESTS PÚBLICOS Y COMPARTIR
    # ============================================================================
    path('tests/publicos/', views.test_public_list, name='test_public_list'),
    path('tests/<int:test_id>/copiar/', views.test_copy, name='test_copy'),
    path('tests/<int:test_id>/hacer-publico/', views.test_make_public, name='test_make_public'),
    
    # ============================================================================
    # JUEGOS EDUCATIVOS
    # ============================================================================
    path('games/memory/', views.game_memory, name='game_memory'),
    path('games/crossword/', views.game_crossword, name='game_crossword'),
    path('games/classification/', views.game_classification, name='game_classification'),
    path('games/quiz-ecosystem/', views.game_quiz_ecosystem, name='game_quiz_ecosystem'),
    path('games/food-chain/', views.game_food_chain, name='game_food_chain'),
    
    # ============================================================================
    # APIs PARA JUEGOS EDUCATIVOS
    # ============================================================================
    path('api/game/complete/', views.api_game_complete, name='api_game_complete'),
    path('api/game/stats/', views.api_get_game_stats, name='api_get_game_stats'),
]

