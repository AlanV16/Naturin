from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    # ========== AUTENTICACIÓN ==========
    path('login/', views.login_unificado, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='users:login'), name='logout'),
    
    # ========== REGISTRO POR TIPO DE USUARIO ==========
    path('registro/estudiante/', views.register_student, name='register_student'),
    path('registro/docente/', views.register_teacher, name='register_teacher'),
    path('registro/padre/', views.register_parent, name='register_parent'),
    
    # ========== VERIFICACIÓN DE EMAIL ==========
    path('verificar-email/<int:user_id>/', views.verify_email, name='verify_email'),
    path('reenviar-codigo/<int:user_id>/', views.resend_verification_code, name='resend_verification_code'),

    # ========== REDIRECCIONES ==========
    path('perfil/', views.redirect_to_user_dashboard, name='profile'),
    path('', views.home_redirect, name='home'),
    
    # ========== DASHBOARDS ==========
    path('dashboard/estudiante/<int:user_id>/', views.dashboard_student, name='dashboard_student'),
    path('dashboard/docente/<int:user_id>/', views.dashboard_teacher, name='dashboard_teacher'),
    path('dashboard/padre/<int:user_id>/', views.dashboard_parent, name='dashboard_parent'),
    path('dashboard/admin/<int:user_id>/', views.dashboard_admin, name='dashboard_admin'),
    
    # ========== RECUPERACIÓN DE CONTRASEÑA (CON CÓDIGO) ==========
    path('olvide-contraseña/', views.password_reset_request, name='password_reset_request'),
    path('verificar-reset/<int:user_id>/', views.password_reset_verify, name='password_reset_verify'),
    path('nueva-contraseña/<int:user_id>/<str:code>/', views.password_reset_form, name='password_reset_form'),
    path('contraseña-actualizada/', views.password_reset_complete, name='password_reset_complete'),
    path('reenviar-codigo-reset/<int:user_id>/', views.resend_password_reset_code, name='resend_password_reset_code'),
]
