from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    # URLs principales de gamificación
    path('dashboard/', views.gamification_dashboard, name='gamification_dashboard'),
    path('test-activity/', views.test_activity_completion, name='test_activity_completion'),
    path('user-stats/', views.user_stats, name='user_stats'),
    path('achievements/', views.achievements_list, name='achievements_list'),
    
    # URLs existentes
    path('', views.dashboard, name='dashboard'),
    path('games/', views.game_list, name='game_list'),
    path('aula/create/', views.aula_create, name='aula_create'),
    path('aula/list/', views.aula_list, name='aula_list'),
    path('aula/<int:aula_id>/', views.aula_detail, name='aula_detail'),
    path('aula/<int:aula_id>/actividad/create/', views.actividad_create, name='actividad_create'),
    path('actividad/<int:actividad_id>/', views.actividad_detail, name='actividad_detail'),
    path('desafios/', views.desafios_list, name='desafios_list'),
    path('desafio/<int:desafio_id>/', views.desafio_detail, name='desafio_detail'),
    path('rankings/', views.rankings_list, name='rankings_list'),
    path('estadisticas/', views.estadisticas_personales, name='estadisticas_personales'),
    path('game/create/', views.game_create, name='game_create'),
    path('game/<int:game_id>/edit/', views.game_edit, name='game_edit'),
    path('game/<int:game_id>/play/', views.quiz_play, name='quiz_play'),
    path('game/<int:game_id>/rapid/', views.rapid_questions_play, name='rapid_questions_play'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('leaderboard/<int:game_id>/', views.leaderboard, name='leaderboard_game'),
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/<str:username>/', views.user_profile, name='user_profile_username'),
    path('api/question-data/<int:game_id>/', views.api_question_data, name='api_question_data'),
    path('api/submit-answer/<int:session_id>/', views.api_submit_answer, name='api_submit_answer'),
    path('notifications/count/', views.notifications_count, name='notifications_count'),
    path('notifications/ajax/', views.notifications_ajax, name='notifications_ajax'),
    
    # URLs de tests
    path('tests/', views.test_list, name='test_list'),
    path('tests/create/', views.test_create, name='test_create'),
    path('tests/<int:test_id>/edit/', views.test_edit, name='test_edit'),
    path('tests/<int:test_id>/', views.test_detail, name='test_detail'),
    path('tests/<int:test_id>/results/', views.test_results, name='test_results'),
    path('tests/<int:test_id>/delete/', views.test_delete, name='test_delete'),
    path('tests/<int:test_id>/pregunta/create/', views.pregunta_create, name='pregunta_create'),
    path('pregunta/<int:pregunta_id>/edit/', views.pregunta_edit, name='pregunta_edit'),
    path('pregunta/<int:pregunta_id>/delete/', views.pregunta_delete, name='pregunta_delete'),
    path('student/tests/', views.student_test_list, name='student_test_list'),
    path('student/tests/<int:test_id>/take/', views.take_test, name='take_test'),
    path('student/tests/<int:test_id>/submit/', views.submit_test, name='submit_test'),
    path('student/tests/<int:test_id>/result/', views.test_result, name='test_result'),
    path('student/tests/results/<int:resultado_id>/', views.test_results_detail, name='test_results_detail'),
    path('tests/<int:test_id>/export/', views.test_export_results, name='test_export_results'),
    path('tests/<int:test_id>/duplicate/', views.test_duplicate, name='test_duplicate'),
    
    # URLs de juegos específicos
    path('games/memory/', views.game_memory, name='game_memory'),
    path('games/crossword/', views.game_crossword, name='game_crossword'),
    path('games/classification/', views.game_classification, name='game_classification'),
    path('games/quiz-ecosystem/', views.game_quiz_ecosystem, name='game_quiz_ecosystem'),
    path('games/food-chain/', views.game_food_chain, name='game_food_chain'),
    path('api/game-complete/', views.api_game_complete, name='api_game_complete'),
    path('api/game-stats/', views.api_get_game_stats, name='api_get_game_stats'),
    
    # URLs de mensajería
    path('messaging/', views.messaging_dashboard, name='messaging_dashboard'),
    path('conversations/', views.private_conversation_list, name='private_conversation_list'),
    path('conversations/<int:conversation_id>/', views.private_conversation_detail, name='private_conversation_detail'),
    path('conversations/new/', views.new_private_message, name='new_private_message'),
    path('search-users/', views.search_users, name='search_users'),
    path('classroom/<int:classroom_id>/chat/', views.classroom_chat, name='classroom_chat'),
    path('message-notifications/', views.message_notifications, name='message_notifications'),
    path('api/unread-count/', views.get_unread_count_api, name='get_unread_count_api'),
    path('api/new-messages/<int:conversation_id>/', views.get_new_messages_api, name='get_new_messages_api'),
    
    # URLs de actividades
    path('assignment/create/', views.assignment_create, name='assignment_create'),
]

