from django.urls import path
from django.contrib.auth import views as auth_views
from . import views 
from django.shortcuts import redirect

app_name = 'accounts'

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
    path('logout/', auth_views.LogoutView.as_view(next_page='accounts:login_student'), name='logout'),

    # Perfil
    path('dashboard/', views.dashboard_student, name='dashboard_student'),
    path('perfil/', lambda request: redirect('accounts:dashboard_student'), name='profile'),

    # Password reset (opcional)
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset_form.html'), name='password_reset'),
]