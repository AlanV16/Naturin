from django.urls import path
from django.contrib.auth import views as auth_views
from . import views 
from django.shortcuts import redirect

app_name = 'users'

urlpatterns = [
    # ========== AUTENTICACIÓN ==========
    path('login/', views.login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='users:login'), name='logout'),

    # Registro por tipo de usuario
    path('registro/estudiante/', views.register_student, name='register_student'),
    path('registro/docente/', views.register_teacher, name='register_teacher'),
    path('registro/padre/', views.register_parent, name='register_parent'),
    path('registro/expert/', views.register_expert, name='register_expert'),

    # ========== VERIFICACIÓN DE EMAIL ==========
    path('verificar-email/<int:user_id>/', views.verify_email, name='verify_email'),
    path('reenviar-codigo/<int:user_id>/', views.resend_verification_code, name='resend_verification_code'),

    # ========== REDIRECCIONES ==========
    path('perfil/', views.redirect_to_user_dashboard, name='profile'),
    path('', views.home_redirect, name='home'),

    # ========== RECUPERACIÓN DE CONTRASEÑA ==========
    path('olvide-contraseña/', views.password_reset_request, name='password_reset_request'),
    path('verificar-reset/<int:user_id>/', views.password_reset_verify, name='password_reset_verify'),
    path('nueva-contraseña/<int:user_id>/<str:code>/', views.password_reset_form, name='password_reset_form'),
    path('contraseña-actualizada/', views.password_reset_complete, name='password_reset_complete'),
    path('reenviar-codigo-reset/<int:user_id>/', views.resend_password_reset_code, name='resend_password_reset_code'),

    # Dashboards
    path('dashboard/estudiante/<int:user_id>/', views.dashboard_student, name='dashboard_student'),
    path('dashboard/docente/<int:user_id>/', views.dashboard_teacher, name='dashboard_teacher'),
    path('dashboard/padre/<int:user_id>/', views.dashboard_parent, name='dashboard_parent'),
    path('dashboard/experto/<int:user_id>/', views.dashboard_expert, name='dashboard_expert'),
    path('dashboard/admin/<int:user_id>/', views.dashboard_admin, name='dashboard_admin'),

    # Perfil (redirecciones)
    path('perfil/student/', lambda request: redirect('users:dashboard_student'), name='profile'),
    path('perfil/teacher/', lambda request: redirect('users:dashboard_teacher'), name='profile_teacher'),
    path('perfil/parent/', lambda request: redirect('users:dashboard_parent'), name='profile_parent'),
    path('perfil/admin/', lambda request: redirect('users:dashboard_admin'), name='profile_admin'),

    # Secciones del estudiante
    path('student/courses/', views.student_courses, name='student_courses'),
    path('student/grades/', views.student_grades, name='student_grades'),
    path('student/achievements/', views.student_achievements, name='student_achievements'),
    path('student/achievement-repository/', views.student_achievement_repository, name='achievement_repository'),
    path('student/assignments/', views.student_assignments, name='student_assignments'),
    path('student/schedule/', views.student_schedule, name='student_schedule'),
    path('student/resources/', views.student_resources, name='student_resources'),
    
    # Profesor
    path('teacher/courses/', views.teacher_courses, name='teacher_courses'),
    path('teacher/assignments/', views.teacher_assignments, name='teacher_assignments'),
    path('teacher/grades/', views.teacher_grades, name='teacher_grades'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),
    path('teacher/resources/', views.teacher_resources, name='teacher_resources'),
    path('teacher/achievements/', views.teacher_achievements, name='teacher_achievements'),
    path('teacher/achievement-repository/', views.teacher_achievement_repository, name='teacher_achievement_repository'),
    path('teacher/schedule/', views.teacher_schedule, name='teacher_schedule'),         
    path('teacher/create-course/', views.create_course, name='create_course'),

    # Expert URLs
    path('expert/review-sheets/', views.expert_review_sheets, name='expert_review_sheets'),
    path('expert/statistics/', views.expert_statistics, name='expert_statistics'),
    path('expert/create-sheet/', views.create_educational_sheet, name='create_educational_sheet'),
    path('expert/generate-report/', views.generate_expert_report, name='generate_expert_report'),
    path('expert/download-report/', views.download_expert_report, name='download_expert_report'),

    # APIs para funcionalidades de docente
    path('api/teacher/create-event/', views.create_event_api, name='create_event_api'),
    path('api/teacher/send-message/', views.send_message_api, name='send_message_api'),
    path('api/teacher/student-details/<int:student_id>/', views.get_student_details_api, name='get_student_details_api'),

    # Notificaciones
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/api/', views.notifications_api, name='notifications_api'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # Acciones específicas
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('course/<int:course_id>/students/', views.course_students, name='course_students'),
    path('course/<int:course_id>/assignments/', views.course_assignments, name='course_assignments'),
    path('course/<int:course_id>/materials/', views.course_materials, name='course_materials'),
    path('course/<int:course_id>/upload-material/', views.upload_material, name='upload_material'),
    path('material/<int:material_id>/delete/', views.delete_material, name='delete_material'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset_form.html'), name='password_reset'),
    path('update-avatar/', views.update_avatar, name='update_avatar'),
    path('calendar/', views.user_calendar, name='user_calendar'),
    path('calendar/partial/', views.calendar_partial, name='calendar_partial'),    # ============================================================================

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
    path('join/<str:code>/', views.join_course_link, name='join_course_link'),


    # SISTEMA DE MENSAJERÍA
    # Vista principal de mensajería (todos los roles)
    path('messages/', views.messages_home, name='messages_home'),
    
    # APIs para mensajería
    path('messages/conversations/', views.get_conversations, name='get_conversations'),
    path('messages/conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('messages/conversation/<int:conversation_id>/messages/', views.get_conversation_messages, name='get_conversation_messages'),
    path('messages/conversation/<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('messages/conversation/<int:conversation_id>/mark-read/', views.mark_messages_read, name='mark_messages_read'),
    path('messages/conversation/<int:conversation_id>/check-new/', views.check_new_messages, name='check_new_messages'),
    path('messages/conversation/<int:conversation_id>/typing/', views.typing_indicator, name='typing_indicator'),
    path('messages/conversation/<int:conversation_id>/stop-typing/', views.stop_typing_indicator, name='stop_typing_indicator'),
    
    # Gestión de contactos
    path('messages/start/', views.start_conversation, name='start_conversation'),
    path('messages/contacts/', views.get_contacts, name='get_contacts'),
    path('messages/add-contact/', views.add_contact, name='add_contact'),
    path('messages/contact-request/<int:request_id>/respond/', views.respond_contact_request, name='respond_contact_request'),
    path('messages/search-users/', views.search_users, name='search_users'),

    # URLs para assignments
    path('course/<int:course_id>/create-assignment/', views.create_assignment, name='create_assignment'),
    path('assignment/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('assignment/<int:assignment_id>/submissions/', views.assignment_submissions, name='assignment_submissions'),

    # ========== ADMINISTRACIÓN DE USUARIOS ==========
    path('admin/users/', views.admin_user_management, name='admin_user_management'),
    path('admin/users/create/', views.admin_create_user, name='admin_create_user'),
    path('admin/users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('admin/users/<int:user_id>/delete/', views.admin_user_delete, name='admin_user_delete'),
]