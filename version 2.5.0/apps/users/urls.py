from django.urls import path
from django.contrib.auth import views as auth_views
from . import views 
from django.shortcuts import redirect

app_name = 'users'

urlpatterns = [
    # Login por tipo de usuario
    path('login/estudiante/', views.login_student, name='login_student'),
    path('login/docente/', views.login_teacher, name='login_teacher'),
    path('login/padre/', views.login_parent, name='login_parent'),
    path('login/admin/', views.login_admin, name='login_admin'),

    # Registro por tipo de usuario
    path('registro/estudiante/', views.register_student, name='register_student'),
    path('registro/docente/', views.register_teacher, name='register_teacher'),
    path('registro/padre/', views.register_parent, name='register_parent'),

    # Logout
    path('logout/', auth_views.LogoutView.as_view(next_page='users:login_student'), name='logout'),

    path('dashboard/student/', views.dashboard_student, name='dashboard_student'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/teacher/', views.dashboard_teacher, name='dashboard_teacher'),
    path('dashboard/parent/', views.dashboard_parent, name='dashboard_parent'),

    # Perfil (redirecciones)
    path('perfil/student/', lambda request: redirect('users:dashboard_student'), name='profile'),
    path('perfil/admin/', lambda request: redirect('users:dashboard_admin'), name='profile_admin'),
    path('perfil/teacher/', lambda request: redirect('users:dashboard_teacher'), name='profile_teacher'),
    path('perfil/parent/', lambda request: redirect('users:dashboard_parent'), name='profile_parent'),

    # Password reset (opcional)
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset_form.html'), name='password_reset'),
]