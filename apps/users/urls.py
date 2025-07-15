from django.urls import path
from django.contrib.auth import views as auth_views
from . import views 
from django.shortcuts import redirect

app_name = 'users'

urlpatterns = [
    # ========== AUTENTICACIÓN ==========
    path('login/', views.login_unificado, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='users:login'), name='logout'),

    # Registro por tipo de usuario
    path('registro/estudiante/', views.register_student, name='register_student'),
    path('registro/docente/', views.register_teacher, name='register_teacher'),
    path('registro/padre/', views.register_parent, name='register_parent'),

    # ========== VERIFICACIÓN DE EMAIL ==========
    path('verificar-email/<int:user_id>/', views.verify_email, name='verify_email'),
    path('reenviar-codigo/<int:user_id>/', views.resend_verification_code, name='resend_verification_code'),

    # ========== REDIRECCIONES ==========
    path('perfil/', views.redirect_to_user_dashboard, name='profile'),
    path('', views.home_redirect, name='home'),

    # ========== RECUPERACIÓN DE CONTRASEÑA (CON CÓDIGO) ==========
    path('olvide-contraseña/', views.password_reset_request, name='password_reset_request'),
    path('verificar-reset/<int:user_id>/', views.password_reset_verify, name='password_reset_verify'),
    path('nueva-contraseña/<int:user_id>/<str:code>/', views.password_reset_form, name='password_reset_form'),
    path('contraseña-actualizada/', views.password_reset_complete, name='password_reset_complete'),
    path('reenviar-codigo-reset/<int:user_id>/', views.resend_password_reset_code, name='resend_password_reset_code'),

    # Dashboards
    path('dashboard/estudiante/<int:user_id>/', views.dashboard_student, name='dashboard_student'),
    path('dashboard/docente/<int:user_id>/', views.dashboard_teacher, name='dashboard_teacher'),
    path('dashboard/padre/<int:user_id>/', views.dashboard_parent, name='dashboard_parent'),
    path('add-child-ajax/', views.add_child_ajax, name='add_child_ajax'),
    path('dashboard/admin/<int:user_id>/', views.dashboard_admin, name='dashboard_admin'),

    # Perfil (redirecciones)
    path('perfil/student/', lambda request: redirect('users:dashboard_student'), name='profile'),
    path('perfil/admin/', lambda request: redirect('users:dashboard_admin'), name='profile_admin'),
    path('perfil/teacher/', lambda request: redirect('users:dashboard_teacher'), name='profile_teacher'),
    path('perfil/parent/', lambda request: redirect('users:dashboard_parent'), name='profile_parent'),

    # Secciones del estudiante
    path('student/courses/', views.student_courses, name='student_courses'),
    path('student/grades/', views.student_grades, name='student_grades'),
    path('student/messages/', views.student_messages, name='student_messages'),
    path('student/calendar/', views.student_calendar, name='student_calendar'),
    path('student/achievements/', views.student_achievements, name='student_achievements'),
    path('student/achievement-repository/', views.student_achievement_repository, name='achievement_repository'),
    path('student/assignments/', views.student_assignments, name='student_assignments'),
    path('student/schedule/', views.student_schedule, name='student_schedule'),
    path('student/resources/', views.student_resources, name='student_resources'),
    
    # ============================================================================
    # VISTAS DE DOCENTE
    # ============================================================================
    path('teacher/courses/', views.teacher_courses, name='teacher_courses'),
    path('teacher/assignments/', views.teacher_assignments, name='teacher_assignments'),
    path('teacher/tests/', views.teacher_tests, name='teacher_tests'),
    path('teacher/readings/', views.teacher_readings, name='teacher_readings'),
    path('teacher/games/', views.teacher_games, name='teacher_games'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),
    path('teacher/grades/', views.teacher_grades, name='teacher_grades'),
    path('teacher/calendar/', views.teacher_calendar, name='teacher_calendar'),
    path('teacher/messages/', views.teacher_messages, name='teacher_messages'),
    path('teacher/resources/', views.teacher_resources, name='teacher_resources'),
    path('teacher/achievements/', views.teacher_achievements, name='teacher_achievements'),
    path('teacher/achievement-repository/', views.teacher_achievement_repository, name='teacher_achievement_repository'),
    path('teacher/schedule/', views.teacher_schedule, name='teacher_schedule'),

    # Vistas mejoradas para gestión de contenido educativo
    path('teacher/tests-enhanced/', views.teacher_tests_enhanced, name='teacher_tests_enhanced'),
    path('teacher/readings-enhanced/', views.teacher_readings_enhanced, name='teacher_readings_enhanced'),
    path('teacher/games-enhanced/', views.teacher_games_enhanced, name='teacher_games_enhanced'),

    # APIs para funcionalidades de docente
    path('api/teacher/create-event/', views.create_event_api, name='create_event_api'),
    path('api/teacher/send-message/', views.send_message_api, name='send_message_api'),
    path('api/teacher/student-details/<int:student_id>/', views.get_student_details_api, name='get_student_details_api'),
    path('api/create-test/', views.create_test_api, name='create_test_api'),
    path('api/assign-reading/', views.assign_reading_api, name='assign_reading_api'),
    path('api/assign-game/', views.assign_game_api, name='assign_game_api'),

    # APIs para mensajería
    path('api/message/<int:message_id>/', views.get_message_api, name='get_message_api'),
    path('api/conversation/<int:conversation_id>/', views.get_conversation_api, name='get_conversation_api'),
    path('api/send-message/', views.send_message_student_api, name='send_message_student_api'),
    path('api/mark-read/<int:message_id>/', views.mark_message_read_api, name='mark_message_read_api'),

    # Notificaciones
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/api/', views.notifications_api, name='notifications_api'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # Notificaciones en tiempo real
    path('notifications/realtime/', views.notifications_realtime_api, name='notifications_realtime_api'),
    path('notifications/create/', views.create_notification_api, name='create_notification_api'),
    path('notifications/mark-read-realtime/<int:notification_id>/', views.mark_notification_read_realtime, name='mark_notification_read_realtime'),
    path('notifications/mark-all-read-realtime/', views.mark_all_notifications_read_realtime, name='mark_all_notifications_read_realtime'),
    path('classroom/<int:class_id>/notify/', views.send_classroom_notification, name='send_classroom_notification'),
    path('notification-settings/', views.notification_settings, name='notification_settings'),

    # Acciones específicas
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    # Password reset (opcional)
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset_form.html'), name='password_reset'),
    path('update-avatar/', views.update_avatar, name='update_avatar'),
    path('calendar/', views.user_calendar, name='user_calendar'),

    # ============================================================================
    # AULAS VIRTUALES
    # ============================================================================
    path('create-class/', views.create_class, name='create_class'),
    path('class/student/<int:class_id>/', views.class_student, name='class_student'),
    path('class/teacher/<int:class_id>/', views.class_teacher, name='class_teacher'),
    path('play-game/<int:class_id>/', views.play_game, name='play_game'),

    # URLs para gestión de cursos
    path('api/generate-class-code/', views.generate_class_code, name='generate_class_code'),
    path('api/create-class/', views.create_class_api, name='create_class_api'),
    path('api/join-class/', views.join_class_api, name='join_class_api'),
    path('api/create-activity/', views.create_activity_api, name='create_activity_api'),
    path('join-class/', views.join_class, name='join_class'),

    # ============================================================================
    # MENSAJERÍA
    # ============================================================================
    path('messages/', views.messages_list, name='messages_list'),
    path('messages/conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('messages/start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('class/<int:class_id>/chat/', views.class_chat, name='class_chat'),
    path('class/<int:class_id>/chat/api/', views.class_chat_api, name='class_chat_api'),

    # ============================================================================
    # URLs AJAX PARA ACTUALIZACIÓN PARCIAL DE DASHBOARDS
    # ============================================================================
    
    # Docente
    path('ajax/teacher/courses/', views.ajax_teacher_courses, name='ajax_teacher_courses'),
    path('ajax/teacher/pending-submissions/', views.ajax_teacher_pending_submissions, name='ajax_teacher_pending_submissions'),
    
    # Estudiante
    path('ajax/student/courses/', views.ajax_student_courses, name='ajax_student_courses'),
    path('ajax/student/achievements/', views.ajax_student_achievements, name='ajax_student_achievements'),
    
    # Padre de familia
    path('ajax/parent/children/', views.ajax_parent_children, name='ajax_parent_children'),
    
    # Administrador
    path('ajax/admin/users/', views.ajax_admin_users, name='ajax_admin_users'),

    # URLs AJAX para Dashboard de Padres
    path('ajax/children-list/', views.ajax_children_list, name='ajax_children_list'),
    path('ajax/add-child/', views.ajax_add_child, name='ajax_add_child'),
    path('ajax/delete-child/', views.ajax_delete_child, name='ajax_delete_child'),
    path('ajax/search-teachers/', views.ajax_search_teachers, name='ajax_search_teachers'),
    path('ajax/teacher-info/<int:teacher_id>/', views.ajax_teacher_info, name='ajax_teacher_info'),
    path('ajax/chat-contacts/', views.ajax_chat_contacts, name='ajax_chat_contacts'),
    path('ajax/chat-messages/<int:contact_id>/', views.ajax_chat_messages, name='ajax_chat_messages'),
    path('ajax/send-message/', views.ajax_send_message, name='ajax_send_message'),
    path('ajax/mark-messages-read/<int:contact_id>/', views.ajax_mark_messages_read, name='ajax_mark_messages_read'),
    path('ajax/unread-messages-count/', views.ajax_unread_messages_count, name='ajax_unread_messages_count'),
    path('ajax/upcoming-events/', views.ajax_upcoming_events, name='ajax_upcoming_events'),
    path('ajax/send-suggestion/', views.ajax_send_suggestion, name='ajax_send_suggestion'),
    path('ajax/suggestions-list/', views.ajax_suggestions_list, name='ajax_suggestions_list'),
    path('ajax/educational-resources/', views.ajax_educational_resources, name='ajax_educational_resources'),
    path('ajax/dashboard-stats/', views.ajax_dashboard_stats, name='ajax_dashboard_stats'),
    path('ajax/recent-activities/', views.ajax_recent_activities, name='ajax_recent_activities'),
    path('ajax/child-progress/<int:child_id>/', views.ajax_child_progress, name='ajax_child_progress'),
    path('ajax/child-assignments/<int:child_id>/', views.ajax_child_assignments, name='ajax_child_assignments'),
    path('ajax/child-grades/<int:child_id>/', views.ajax_child_grades, name='ajax_child_grades'),
    path('ajax/calendar-events/', views.ajax_calendar_events, name='ajax_calendar_events'),
    path('ajax/notifications/', views.ajax_notifications, name='ajax_notifications'),
    path('ajax/mark-all-notifications-read/', views.ajax_mark_all_notifications_read, name='ajax_mark_all_notifications_read'),
    path('ajax/update-profile/', views.ajax_update_profile, name='ajax_update_profile'),
    path('ajax/export-child-report/<int:child_id>/', views.ajax_export_child_report, name='ajax_export_child_report'),
]

# Endpoints AJAX mínimos para dashboard de padres
urlpatterns += [
    path('ajax/recent-activities/', views.ajax_recent_activities, name='ajax_recent_activities'),
    path('ajax/dashboard-stats/', views.ajax_dashboard_stats, name='ajax_dashboard_stats'),
    path('ajax/notifications/', views.ajax_notifications, name='ajax_notifications'),
    path('ajax/children-list/', views.ajax_children_list, name='ajax_children_list'),
]