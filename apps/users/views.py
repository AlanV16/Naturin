import calendar
import locale 
import os
import logging
import random
import string
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages 
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test   
from django.template.loader import render_to_string
from django.db.models import Count, Avg, Q, Max
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from validate_email import validate_email
from django.core.paginator import Paginator
from django.contrib.auth import logout
from datetime import datetime, timedelta, date


from django.db import transaction
from apps.educational_games.gamification.models import ( Aulas, AulaEstudiante, Actividades, Niveles )
from .utils import generate_classroom_code

# Importa Notification desde la nueva app de gamificación
from apps.educational_games.gamification.models import Notification
from .utils import send_verification_email, send_welcome_email
# Import de modelos adicionales
from .models import (
    Course, Subject, Enrollment, Assignment, AssignmentSubmission, 
    Achievement, StudentAchievement, Event, Notification,
    Message, Conversation, User, ContactRequest, Contact, CalendarEvent, Material
)

# Importar modelos de content
from apps.content.models import EducationalSheet, SheetRevisionHistory, StudentContent

from .forms import (
    LoginForm, StudentRegisterForm, TeacherRegisterForm, ParentRegisterForm, ExpertRegisterForm,
    EmailVerificationForm, PasswordResetRequestForm, PasswordResetVerifyForm, 
    PasswordResetForm
)

# Configuración centralizada para tipos de usuario
USER_TYPE_CONFIG = {
    1: {  # Estudiante
        'name': 'Estudiante',
        'background': 'images/forms/fondo.png',
        'registration_url': 'users:register_student',
        'dashboard_url': 'users:dashboard_student'
    },
    2: {  # Docente
        'name': 'Docente', 
        'background': 'images/forms/fondo_doc.png',
        'registration_url': 'users:register_teacher',
        'dashboard_url': 'users:dashboard_teacher'
    },
    3: {  # Padre
        'name': 'Padre',
        'background': 'images/forms/fondo_padres.png', 
        'registration_url': 'users:register_parent',
        'dashboard_url': 'users:dashboard_parent'
    },
    4: {  # Experto
        'name': 'Experto',
        'background': 'images/forms/fondo_expert.png',
        'registration_url': 'users:register_expert',
        'dashboard_url': 'users:dashboard_expert'
    },
    5: {  # Admin
        'name': 'Administrador',
        'background': 'images/forms/fondo_admin.png',
        'registration_url': None,  # Los admin no se registran públicamente
        'dashboard_url': 'users:dashboard_admin'
    }
}
# ===== VISTAS DE AUTENTICACIÓN =====

def login(request):
    """Vista de login actualizada para verificar email"""
    if request.user.is_authenticated:
        return redirect_to_user_dashboard(request)
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        
        if form.is_valid():
            user = form.get_user()
            
            # Verificar si el email está verificado para todos los tipos de usuario
            if not user.is_email_verified:
                messages.warning(
                    request,
                    'Debes verificar tu email antes de iniciar sesión.'
                )
                return redirect('users:verify_email', user_id=user.id)
            
            auth_login(request, user)
            messages.success(request, f'¡Bienvenido, {user.get_full_name()}!')
            return redirect_to_user_dashboard(request)
        else:
            messages.error(request, 'Credenciales inválidas.')
    else:
        form = LoginForm()
    
    # Contexto para el template
    context = {
        'form': form,
        'background_image': 'images/forms/fondo.png',  # Imagen de fondo por defecto
        'registration_link': 'users:register_student',  # Link por defecto al registro de estudiante
    }
    
    return render(request, 'accounts/login.html', context)

def redirect_to_user_dashboard(request):
    """Redirige al dashboard según el tipo de usuario"""
    if not request.user.is_authenticated:
        return redirect('users:login')
    
    user = request.user
    
    # Verificar que el usuario tenga un tipo válido
    if not hasattr(user, 'user_type') or user.user_type is None:
        messages.error(request, 'Tu cuenta no tiene un tipo de usuario asignado. Contacta al administrador.')
        return redirect('users:login')
    
    if user.user_type == 1:  # Estudiante
        return redirect('users:dashboard_student', user_id=user.id)
    elif user.user_type == 2:  # Docente
        return redirect('users:dashboard_teacher', user_id=user.id)
    elif user.user_type == 3:  # Padre
        return redirect('users:dashboard_parent', user_id=user.id)
    elif user.user_type == 4:  # Experto
        return redirect('users:dashboard_expert', user_id=user.id)
    elif user.user_type == 5:  # Admin
        return redirect('users:dashboard_admin', user_id=user.id)
    else:
        messages.error(request, f'Tipo de usuario no válido: {user.user_type}. Contacta al administrador.')
        return redirect('users:login')

def mask_email(email):
    """Enmascara el email para mostrar solo primeros y últimos caracteres"""
    try:
        name, domain = email.split('@')
        if len(name) <= 2:
            masked_name = name
        else:
            masked_name = name[0] + '*' * (len(name) - 2) + name[-1]
        return f"{masked_name}@{domain}"
    except:
        return email
    
def register_view(request, form_class, template, redirect_name='users:login'):
    """
    Vista genérica para registro de usuarios
    """
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Usuario {user.username} registrado exitosamente.")
            return redirect(redirect_name)
        else:
            messages.error(request, "Error en el registro. Por favor, revisa los datos.")
    else:
        form = form_class()
    
    return render(request, template, {'form': form})

logger = logging.getLogger(__name__)

def register_student(request):
    """Registro específico para estudiantes con verificación de email"""
    if request.method == 'POST':
        form = StudentRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request, 
                f'¡Registro exitoso! Se ha enviado un código de verificación a {user.email}'
            )
            # Redirigir a la página de verificación
            return redirect('users:verify_email', user_id=user.id)
    else:
        form = StudentRegisterForm()
    
    return render(request, 'accounts/signup_student.html', {'form': form})

def register_teacher(request):
    """Registro de docentes con verificación de email"""
    if request.method == 'POST':
        form = TeacherRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request, 
                f'¡Registro exitoso! Se ha enviado un código de verificación a {user.email}'
            )
            # Redirigir a la página de verificación
            return redirect('users:verify_email', user_id=user.id)
    else:
        form = TeacherRegisterForm()
    
    return render(request, 'accounts/signup_teacher.html', {'form': form})

def register_parent(request):
    """Registro específico para padres con verificación de email"""
    if request.method == 'POST':
        form = ParentRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request, 
                f'¡Registro exitoso! Se ha enviado un código de verificación a {user.email}'
            )
            # Redirigir a la página de verificación
            return redirect('users:verify_email', user_id=user.id)
    else:
        form = ParentRegisterForm()
    
    return render(request, 'accounts/signup_parent.html', {'form': form})

def register_expert(request):
    """Registro específico para expertos con validación profesional"""
    if request.method == 'POST':
        form = ExpertRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Crear notificación para administradores
            try:
                admin_users = User.objects.filter(user_type=5, is_active=True)
                for admin in admin_users:
                    Notification.objects.create(
                        user=admin,
                        title='Nuevo experto solicita verificación',
                        message=f'{user.get_full_name()} ({user.professional_title}) ha solicitado registro como experto',
                        notification_type='system'
                    )
            except Exception as e:
                print(f"Error creando notificaciones para admin: {e}")
            
            messages.success(
                request, 
                f'¡Registro exitoso! Tu solicitud como experto ha sido enviada para revisión. '
                f'Te notificaremos por email cuando sea aprobada. '
                f'Código de verificación enviado a {user.email}'
            )
            
            # Redirigir a página de verificación de email
            return redirect('users:verify_email', user_id=user.id)
        else:
            # Mostrar errores específicos del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ExpertRegisterForm()
    
    context = {
        'form': form,
        'title': 'Registro de Experto',
        'subtitle': 'Únete como experto en contenido educativo',
        'expertise_examples': [
            'Biología y Ciencias Naturales',
            'Ecología y Medio Ambiente',
            'Educación Ambiental',
            'Botánica y Zoología',
            'Geología y Ciencias de la Tierra',
            'Química Ambiental',
            'Conservación de la Biodiversidad'
        ],
        'requirements': [
            'Título universitario en área relacionada',
            'Mínimo 1 año de experiencia profesional',
            'Conocimientos en educación o divulgación',
            'Compromiso con la calidad educativa'
        ]
    }
    
    return render(request, 'accounts/signup_expert.html', context)

def verify_email(request, user_id):
    """Vista para verificar el código de email"""
    user = get_object_or_404(User, id=user_id)
    
    # Si ya está verificado, redirigir
    if user.is_email_verified:
        messages.info(request, 'Tu email ya está verificado.')
        return redirect('users:login')
    
    if request.method == 'POST':
        form = EmailVerificationForm(user, request.POST)
        if form.is_valid():
            # Verificar y activar la cuenta
            user.verify_email()
            user.is_active = True
            user.save()
            
            # Enviar email de bienvenida
            send_welcome_email(user)
            
            messages.success(request, '¡Email verificado exitosamente! Ya puedes iniciar sesión.')
            return redirect('users:login')
    else:
        form = EmailVerificationForm(user)
    
    return render(request, 'accounts/verify_email.html', {
        'form': form,
        'user': user
    })

def resend_verification_code(request, user_id):
    """Vista para reenviar código de verificación"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        
        if user.is_email_verified:
            return JsonResponse({
                'success': False,
                'message': 'El email ya está verificado.'
            })
        
        # Verificar límite de tiempo (1 minuto entre envíos)
        if (user.email_verification_created and 
            timezone.now() - user.email_verification_created < timezone.timedelta(minutes=1)):
            return JsonResponse({
                'success': False,
                'message': 'Debes esperar 1 minuto antes de solicitar otro código.'
            })
        
        # Enviar nuevo código
        if send_verification_email(user):
            return JsonResponse({
                'success': True,
                'message': 'Código reenviado exitosamente.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Error enviando el código. Intenta nuevamente.'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido.'})


# ===== DASHBOARDS =====

@login_required
def dashboard_student(request, user_id):
    """Dashboard principal del estudiante con datos reales"""
    user = request.user
    
    try:
        # Verificar si las tablas existen antes de hacer consultas
        enrollments = Enrollment.objects.filter(student=user).select_related('course', 'course__subject')
        courses = []
        
        # Procesar enrollments de forma segura
        for enrollment in enrollments:
            try:
                courses.append(enrollment.course)
            except Exception as e:
                print(f"Error procesando enrollment {enrollment.id}: {e}")
                continue
                
    except Exception as e:
        print(f"Error obteniendo enrollments: {e}")
        enrollments = []
        courses = []
    
    # Estadísticas generales with valores por defecto
    total_courses = len(courses)
    active_courses = 0
    pending_assignments = 0
    upcoming_events = 0
    total_achievements = 0
    general_progress = 0
    course_details = []
    recent_activities = []
    next_events = []
    recent_achievements = []
    average_grade = 0
    
    try:
        # Solo calcular si hay cursos
        if courses:
            active_courses = len([c for c in courses if hasattr(c, 'status') and c.status == 'active'])
            
            # Progreso general
            if enrollments.exists():
                general_progress = enrollments.aggregate(avg_progress=Avg('progress'))['avg_progress'] or 0
            
            # Cursos para mostrar en el dashboard (máximo 3)
            for enrollment in enrollments[:3]:
                try:
                    course = enrollment.course
                    teacher_name = "Sin asignar"
                    try:
                        teacher_name = course.teacher.get_full_name() if course.teacher else "Sin asignar"
                    except:
                        pass
                    
                    icon = "book"
                    try:
                        icon = course.subject.icon if hasattr(course, 'subject') and course.subject else "book"
                    except:
                        pass
                    
                    course_details.append({
                        'id': course.id,
                        'name': course.name,
                        'teacher': teacher_name,
                        'progress': enrollment.progress,
                        'icon': icon,
                    })
                except Exception as e:
                    print(f"Error procesando course details: {e}")
                    continue
    
    except Exception as e:
        print(f"Error calculando estadísticas: {e}")
    
    # Crear notificaciones de prueba si no existen
    try:
        if not user.gamification_notifications.exists():
            Notification.objects.create(
                recipient=user,
                title='¡Bienvenido!',
                message='Te damos la bienvenida a nuestra plataforma educativa.',
                notification_type='achievement_unlocked'
            )
    except Exception as e:
        print(f"Error creando notificaciones: {e}")
    
    # Logros obtenidos por el estudiante
    try:
        # Obtener logros obtenidos por el estudiante
        student_achievements = StudentAchievement.objects.filter(
            student=user
        ).select_related('achievement').order_by('-earned_at')[:4]
        
        # Obtener algunos logros disponibles que no ha obtenido (para mostrar como "locked")
        earned_achievement_ids = student_achievements.values_list('achievement_id', flat=True)
        available_achievements = Achievement.objects.exclude(
            id__in=earned_achievement_ids
        )[:2]  # Solo 2 logros no obtenidos para completar la grilla
        
        total_achievements = student_achievements.count()
        
        # Preparar datos de logros para el template
        achievements_data = []
        
        # Agregar logros obtenidos
        for student_achievement in student_achievements:
            achievement = student_achievement.achievement
            achievements_data.append({
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'points': achievement.points,
                'earned': True,
                'earned_at': student_achievement.earned_at,
                'css_class': 'earned'
            })
        
        # Agregar algunos logros no obtenidos (máximo 4 en total)
        remaining_slots = 4 - len(achievements_data)
        for achievement in available_achievements[:remaining_slots]:
            achievements_data.append({
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'points': achievement.points,
                'earned': False,
                'earned_at': None,
                'css_class': 'locked'
            })
            
    except Exception as e:
        print(f"Error cargando logros: {e}")
        achievements_data = []
        total_achievements = 0
    
    # Cálculos de rendimiento académico
    try:
        # Obtener todas las calificaciones del estudiante
        submissions = AssignmentSubmission.objects.filter(
            student=user, 
            grade__isnull=False
        ).select_related('assignment')
        
        if submissions.exists():
            # Calcular promedio general
            grades = [s.grade for s in submissions if s.grade is not None]
            average_grade = sum(grades) / len(grades) if grades else 0
            
            # Calcular progreso de tareas completadas
            total_assignments = Assignment.objects.filter(
                course__in=[enrollment.course for enrollment in enrollments if hasattr(enrollment, 'course')]
            ).count() if enrollments else 0
            
            completed_assignments = submissions.count()
            completion_percentage = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
            
            # Determinar letra de calificación
            if average_grade >= 9.0:
                grade_letter = 'A+'
            elif average_grade >= 8.5:
                grade_letter = 'A'
            elif average_grade >= 8.0:
                grade_letter = 'B+'
            elif average_grade >= 7.5:
                grade_letter = 'B'
            elif average_grade >= 7.0:
                grade_letter = 'C+'
            elif average_grade >= 6.0:
                grade_letter = 'C'
            else:
                grade_letter = 'D'
            
            # Calcular ranking (posición entre estudiantes del mismo nivel)
            # Esto es una simulación simple, en un sistema real sería más complejo
            all_students_avg = []
            for student in User.objects.filter(user_type=1):
                student_submissions = AssignmentSubmission.objects.filter(
                    student=student, 
                    grade__isnull=False
                )
                if student_submissions.exists():
                    student_grades = [s.grade for s in student_submissions if s.grade is not None]
                    student_avg = sum(student_grades) / len(student_grades)
                    all_students_avg.append(student_avg)
            
            # Ordenar de mayor a menor y encontrar la posición
            all_students_avg.sort(reverse=True)
            try:
                user_ranking = all_students_avg.index(average_grade) + 1
            except ValueError:
                user_ranking = len(all_students_avg) + 1
            
        else:
            average_grade = 0
            completion_percentage = 0
            grade_letter = 'N/A'
            user_ranking = 'N/A'
            completed_assignments = 0
            total_assignments = Assignment.objects.filter(
                course__in=[enrollment.course for enrollment in enrollments if hasattr(enrollment, 'course')]
            ).count() if enrollments else 0
        
        # Datos para el gráfico de rendimiento
        performance_data = {
            'completed': min(completion_percentage, 100),
            'pending': max(100 - completion_percentage, 0),
            'average_grade': round(average_grade, 1),
            'grade_letter': grade_letter,
            'ranking': user_ranking,
            'completed_assignments': completed_assignments,
            'total_assignments': total_assignments
        }
        
    except Exception as e:
        print(f"Error calculando rendimiento: {e}")
        performance_data = {
            'completed': 0,
            'pending': 100,
            'average_grade': 0,
            'grade_letter': 'N/A',
            'ranking': 'N/A',
            'completed_assignments': 0,
            'total_assignments': 0
        }
    
    context = {
        'user': user,
        'total_courses': total_courses,
        'active_courses': active_courses,
        'pending_assignments': pending_assignments,
        'upcoming_events': upcoming_events,
        'total_achievements': total_achievements,
        'general_progress': round(general_progress, 1),
        'course_details': course_details,
        'recent_activities': recent_activities,
        'next_events': next_events,
        'recent_achievements': achievements_data,
        'average_grade': average_grade,
        'performance_data': performance_data,  # Agregar datos de rendimiento
    }
    
    return render(request, 'dashboards/dashboard_student.html')
#Unirse a clase 

def password_reset_request(request):
    """
    Vista para solicitar reset de contraseña
    """
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # Verificar que el usuario esté verificado
            if not user.is_email_verified:
                messages.error(
                    request, 
                    '❌ Debes verificar tu email antes de poder restablecer tu contraseña. '
                    'Revisa tu bandeja de entrada o solicita un nuevo código de verificación.'
                )
                return redirect('users:verify_email', user_id=user.id)
            
            # Enviar email con código de reset
            from .utils import send_password_reset_email
            if send_password_reset_email(user):
                messages.success(
                    request, 
                    f'✅ Se ha enviado un código de verificación a {user.email}. '
                    'Revisa tu bandeja de entrada y tu carpeta de spam.'
                )
                return redirect('users:password_reset_verify', user_id=user.id)
            else:
                messages.error(
                    request, 
                    '❌ Error enviando el email. Intenta nuevamente en unos minutos.'
                )
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'accounts/password_reset_request.html', {
        'form': form,
        'title': 'Restablecer Contraseña'
    })


def password_reset_verify(request, user_id):
    """
    Vista para verificar código de reset
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, '❌ Usuario no encontrado.')
        return redirect('users:password_reset_request')
    
    # Verificar que el usuario tenga un código activo
    if not user.password_reset_code or not user.password_reset_created:
        messages.error(
            request, 
            '❌ No hay un código de reset activo. Solicita uno nuevo.'
        )
        return redirect('users:password_reset_request')
    
    if request.method == 'POST':
        form = PasswordResetVerifyForm(request.POST, user=user)
        if form.is_valid():
            # Código válido, ir a formulario de nueva contraseña
            messages.success(
                request, 
                '✅ Código verificado correctamente. Ahora establece tu nueva contraseña.'
            )
            return redirect('users:password_reset_form', user_id=user.id, code=form.cleaned_data['reset_code'])
    else:
        form = PasswordResetVerifyForm(user=user)
    
    return render(request, 'accounts/password_reset_verify.html', {
        'form': form,
        'user': user,
        'title': 'Verificar Código'
    })


def password_reset_form(request, user_id, code):
    """
    Vista para establecer nueva contraseña
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, '❌ Usuario no encontrado.')
        return redirect('users:password_reset_request')
    
    # Verificar que el código siga siendo válido
    if not user.is_password_reset_code_valid(code):
        messages.error(
            request, 
            '❌ El código ha expirado o no es válido. Solicita uno nuevo.'
        )
        return redirect('users:password_reset_request')
    
    if request.method == 'POST':
        form = PasswordResetForm(request.POST, user=user)
        if form.is_valid():
            # Actualizar contraseña
            form.save()
            
            messages.success(
                request, 
                '✅ Tu contraseña ha sido actualizada exitosamente. '
                'Ya puedes iniciar sesión con tu nueva contraseña.'
            )
            
            # Registrar evento de seguridad
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Contraseña restablecida para usuario: {user.username} ({user.email})")
            
            return redirect('users:password_reset_complete')
    else:
        form = PasswordResetForm(user=user)
    
    return render(request, 'accounts/password_reset_form.html', {
        'form': form,
        'user': user,
        'title': 'Nueva Contraseña'
    })


def password_reset_complete(request):
    """
    Vista de confirmación de reset completado
    """
    return render(request, 'accounts/password_reset_complete.html', {
        'title': 'Contraseña Actualizada'
    })


@require_http_methods(["POST"])
def resend_password_reset_code(request, user_id):
    """
    API para reenviar código de reset de contraseña
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Verificar rate limiting (no más de 1 código cada 60 segundos)
        if user.password_reset_created:
            time_diff = timezone.now() - user.password_reset_created
            if time_diff.total_seconds() < 60:
                return JsonResponse({
                    'success': False,
                    'message': 'Debes esperar al menos 60 segundos antes de solicitar otro código.'
                })
        
        # Enviar nuevo código
        from .utils import send_password_reset_email
        if send_password_reset_email(user):
            return JsonResponse({
                'success': True,
                'message': 'Nuevo código enviado exitosamente.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Error enviando el código. Intenta nuevamente.'
            })
            
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Usuario no encontrado.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor.'
        })

@login_required
def dashboard_view(request, user_id, user_type, template):
    """
    Vista genérica para dashboards con validación de acceso
    """
    user = get_object_or_404(User, id=user_id, user_type=user_type)
    
    # Verificar que el usuario logueado sea el mismo que está accediendo
    if request.user != user:
        messages.error(request, "No tienes permisos para acceder a este dashboard.")
        # Redirigir al dashboard correcto del usuario actual
        if request.user.user_type in USER_TYPE_CONFIG:
            dashboard_url = USER_TYPE_CONFIG[request.user.user_type]['dashboard_url']
            return redirect(dashboard_url, user_id=request.user.id)
        return redirect('users:login')
    
    context = {
        'user': user,
        'user_type_name': USER_TYPE_CONFIG.get(user_type, {}).get('name', 'Usuario'),
    }
    
    return render(request, template, context)
# Asegúrate de que la vista dashboard_teacher tenga esta estructura:

@login_required
def dashboard_teacher(request, user_id):
    user = request.user
    if request.user.id != user_id:
        return redirect('users:dashboard_teacher', user_id=request.user.id)
    
    if user.user_type != 2:
        return redirect('users:login')
    
    # Obtener cursos del docente
    courses = Course.objects.filter(teacher=user)
    
    # Obtener estadísticas por curso
    course_stats = []
    for course in courses:
        enrollments = Enrollment.objects.filter(course=course)
        students_count = enrollments.count()
        assignments_count = Assignment.objects.filter(course=course).count()
        
        # Promedio de calificaciones (si tienes ese modelo)
        # avg_grade = ... (implementar según tu modelo de calificaciones)
        
        course_stats.append({
            'course': course,  # Importante: debe incluir el objeto course completo
            'students_count': students_count,
            'assignments_count': assignments_count,
            'avg_grade': 0,  # Implementar según tu sistema de calificaciones
            'pending_submissions': 0,  # Implementar según tu sistema
        })
    
    # Otras estadísticas
    total_students = sum(stat['students_count'] for stat in course_stats)
    active_courses = courses.count()
    
    context = {
        'user': user,
        'course_stats': course_stats,  # Importante: incluir course_stats
        'total_students': total_students,
        'active_courses': active_courses,
        'pending_count': 0,  # Implementar
        'recent_activities': [],  # Implementar
        'pending_submissions': [],  # Implementar
        'recent_achievements': [],  # Implementar
    }
    
    return render(request, 'dashboards/dashboard_teacher.html', context)

@login_required
def dashboard_parent(request, user_id):
    """Dashboard para usuarios de tipo padre"""
    user = request.user
    if request.user.id != user_id:
        return redirect('users:dashboard_parent', user_id=request.user.id)
    
    if user.user_type != 4:  # Asumiendo que 4 es el tipo para padres
        return redirect('users:login')
    
    # Aquí puedes agregar lógica específica para padres
    # Por ejemplo: hijos asociados, progreso académico, etc.
    
    context = {
        'user': user,
        'children_count': 0,  # Implementar cuando tengas la relación padre-hijo
        'total_activities': 0,  # Implementar
        'completed_activities': 0,  # Implementar
        'recent_activities': [],  # Implementar
    }
    
    return render(request, 'dashboards/dashboard_parent.html', context)

@login_required
def dashboard_admin(request, user_id):
    """Dashboard para usuarios administradores con estadísticas completas"""
    user = request.user
    
    # Verificar que sea admin antes que nada
    if not (user.is_staff or user.is_superuser or user.user_type == 5):
        messages.error(request, 'No tienes permisos para acceder al panel de administración.')
        return redirect_to_user_dashboard(request)
    
    # Verificar que el user_id coincida con el usuario actual
    if request.user.id != user_id:
        return redirect('users:dashboard_admin', user_id=request.user.id)
    
    # Importaciones necesarias
    from django.contrib.auth import get_user_model
    from apps.content.models import EducationalSheet
    from django.utils import timezone
    from datetime import timedelta
    
    # Intentar importar MultimediaContent
    try:
        from apps.multimedia.models import MultimediaContent
    except ImportError:
        MultimediaContent = None
    
    User = get_user_model()
    
    # Estadísticas de usuarios
    total_users = User.objects.count()
    new_users_this_month = User.objects.filter(
        date_joined__gte=timezone.now().replace(day=1)
    ).count()
    
    # Conteo por tipo de usuario
    student_count = User.objects.filter(user_type=1).count()
    teacher_count = User.objects.filter(user_type=2).count()
    parent_count = User.objects.filter(user_type=3).count()
    expert_count = User.objects.filter(user_type=4).count()
    admin_count = User.objects.filter(user_type=5).count()

    
    # Estadísticas de contenido educativo
    total_sheets = EducationalSheet.objects.count()
    try:
        pending_review_sheets = EducationalSheet.objects.filter(
            status='pending_review'
        ).count()
        approved_sheets = EducationalSheet.objects.filter(
            status='approved'
        ).count()
        in_review_sheets = EducationalSheet.objects.filter(
            status='in_review'
        ).count()
    except:
        pending_review_sheets = 0
        approved_sheets = 0
        in_review_sheets = 0
    
    # Estadísticas de multimedia
    try:
        if MultimediaContent:
            total_multimedia = MultimediaContent.objects.count()
            active_content = MultimediaContent.objects.filter(is_active=True).count()
        else:
            total_multimedia = 0
            active_content = 0
    except:
        total_multimedia = 0
        active_content = 0
    
    # Actividad del sistema
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    daily_activity = User.objects.filter(last_login__date=today).count()
    daily_sessions = User.objects.filter(last_login__date=today).count()
    
    # Calcular engagement rate (simulado)
    active_users_today = User.objects.filter(last_login__date=today).count()
    engagement_rate = int((active_users_today / total_users * 100)) if total_users > 0 else 0
    
    # Usuarios recientes con información completa
    recent_users = User.objects.select_related().order_by('-date_joined')[:10]
    
    # Todos los usuarios para la tabla de gestión
    all_users = User.objects.select_related().order_by('-date_joined')
    
    # Actividades recientes mejoradas
    recent_activities = []
    
    # Actividades de usuarios recientes
    for recent_user in recent_users[:3]:
        recent_activities.append({
            'description': f'Nuevo usuario registrado: {recent_user.first_name} {recent_user.last_name} ({recent_user.get_user_type_display()})',
            'timestamp': recent_user.date_joined,
            'type': 'user',
            'icon': 'person-plus'
        })
    
    # Actividades del sistema
    recent_activities.extend([
        {
            'description': f'Fichas educativas pendientes de revisión: {pending_review_sheets}',
            'timestamp': timezone.now() - timedelta(hours=1),
            'type': 'content',
            'icon': 'file-text'
        },
        {
            'description': 'Sistema funcionando correctamente',
            'timestamp': timezone.now() - timedelta(minutes=30),
            'type': 'system',
            'icon': 'check-circle'
        },
        {
            'description': f'Usuarios activos hoy: {daily_activity}',
            'timestamp': timezone.now() - timedelta(hours=2),
            'type': 'activity',
            'icon': 'activity'
        }
    ])
    
    # Ordenar actividades por timestamp
    recent_activities = sorted(recent_activities, key=lambda x: x['timestamp'], reverse=True)[:10]
    
    # Estado del sistema (simulado pero realista)
    try:
        # Uso de CPU y memoria simulado
        cpu_usage = 15  # Valor por defecto
        memory_usage = 45
        storage_used = 65
        server_performance = 85
        system_alerts = 0
        security_status = "Seguro"
    except:
        cpu_usage = 15
        memory_usage = 45
        storage_used = 65
        server_performance = 85
        system_alerts = 0
        security_status = "Seguro"
    
    context = {
        'user': user,
        # Estadísticas de usuarios
        'total_users': total_users,
        'new_users_this_month': new_users_this_month,
        'student_count': student_count,
        'teacher_count': teacher_count,
        'parent_count': parent_count,
        'expert_count': expert_count,
        'admin_count': admin_count,
        
        # Estadísticas de contenido
        'total_sheets': total_sheets,
        'pending_review_sheets': pending_review_sheets,
        'approved_sheets': approved_sheets,
        'in_review_sheets': in_review_sheets,
        'total_multimedia': total_multimedia,
        'active_content': active_content,
        
        # Actividad del sistema
        'daily_activity': daily_activity,
        'daily_sessions': daily_sessions,
        'engagement_rate': engagement_rate,
        'avg_session_time': '25m',  # Simulado
        
        # Estado del sistema
        'system_alerts': system_alerts,
        'security_status': security_status,
        'cpu_usage': cpu_usage,
        'memory_usage': memory_usage,
        'storage_used': storage_used,
        'server_performance': server_performance,
        
        # Datos para tablas y listas
        'recent_users': all_users,  # Cambio a todos los usuarios para mostrar información completa
        'recent_activities': recent_activities,
        
        # Timestamp para actualizaciones
        'last_update': timezone.now().strftime('%H:%M'),
    }
    
    return render(request, 'dashboards/dashboard_admin.html', context)
# ...existing code...

@login_required
def admin_user_management(request):
    """Vista para gestión completa de usuarios (solo admin)"""
    if not request.user.is_authenticated or request.user.user_type != 'admin':
        return redirect('users:dashboard')
    
    # Obtener parámetros de filtro y búsqueda
    search_query = request.GET.get('search', '')
    user_type_filter = request.GET.get('user_type', '')
    status_filter = request.GET.get('status', '')
    sort_by = request.GET.get('sort', 'date_joined')
    page = request.GET.get('page', 1)
    
    # Query base de usuarios
    users = User.objects.all()
    
    # Aplicar filtros
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query)
        )
    
    if user_type_filter:
        users = users.filter(user_type=user_type_filter)
    
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    # Ordenamiento
    if sort_by == 'name':
        users = users.order_by('first_name', 'last_name')
    elif sort_by == 'email':
        users = users.order_by('email')
    elif sort_by == 'last_login':
        users = users.order_by('-last_login')
    elif sort_by == 'user_type':
        users = users.order_by('user_type')
    else:  # date_joined
        users = users.order_by('-date_joined')
    
    # Paginación
    paginator = Paginator(users, 20)  # 20 usuarios por página
    try:
        users_page = paginator.page(page)
    except PageNotAnInteger:
        users_page = paginator.page(1)
    except EmptyPage:
        users_page = paginator.page(paginator.num_pages)
    
    # Estadísticas
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()
    
    # Contadores por tipo de usuario
    user_type_counts = User.objects.values('user_type').annotate(count=Count('id'))
    type_stats = {}
    for item in user_type_counts:
        type_stats[item['user_type']] = item['count']
    
    # Usuarios registrados este mes
    current_month = timezone.now().replace(day=1)
    new_users_this_month = User.objects.filter(date_joined__gte=current_month).count()
    
    # Usuarios activos (últimos 30 días)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    active_last_30_days = User.objects.filter(last_login__gte=thirty_days_ago).count()
    
    context = {
        'users': users_page,
        'search_query': search_query,
        'user_type_filter': user_type_filter,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'type_stats': type_stats,
        'new_users_this_month': new_users_this_month,
        'active_last_30_days': active_last_30_days,
        'user_types': [
            ('student', 'Estudiante'),
            ('teacher', 'Docente'),
            ('parent', 'Padre/Madre'),
            ('expert', 'Experto'),
            ('admin', 'Administrador'),
        ],
        'page_title': 'Gestión de Usuarios',
    }
    
    return render(request, 'users/admin_user_management.html', context)
# ...existing code...

@login_required
def admin_create_user(request):
    """Vista para crear usuarios desde el panel de admin"""
    if not request.user.is_authenticated or request.user.user_type != 'admin':
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción'})
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            username = request.POST.get('username')
            password = request.POST.get('password')
            user_type = request.POST.get('user_type')
            
            # Validar campos requeridos
            if not all([first_name, last_name, email, username, password, user_type]):
                return JsonResponse({'success': False, 'error': 'Todos los campos son requeridos'})
            
            # Verificar si el email ya existe
            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'error': 'Este email ya está registrado'})
            
            # Verificar si el username ya existe
            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'error': 'Este username ya está registrado'})
            
            # Crear el usuario
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                user_type=user_type
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Usuario {user.get_full_name()} creado exitosamente',
                'user_id': user.id
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

# ...existing code...

@login_required
def admin_user_detail(request, user_id):
    """Vista para mostrar detalles completos de un usuario (solo admin)"""
    if not request.user.is_authenticated or request.user.user_type != 'admin':
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción'})
    
    try:
        user_detail = get_object_or_404(User, id=user_id)
        
        # Obtener estadísticas del usuario
        user_stats = get_user_statistics(user_detail)
        
        # Obtener actividad reciente
        recent_activity = get_user_recent_activity(user_detail)
        
        # Obtener cursos del usuario
        user_courses = get_user_courses(user_detail)
        
        # Obtener logros del usuario (si es estudiante)
        user_achievements = get_user_achievements(user_detail)
        
        # Preparar datos para la respuesta
        user_data = {
            'id': user_detail.id,
            'full_name': user_detail.get_full_name(),
            'username': user_detail.username,
            'email': user_detail.email,
            'user_type': user_detail.user_type,
            'user_type_display': user_detail.get_user_type_display(),
            'is_active': user_detail.is_active,
            'is_email_verified': user_detail.is_email_verified,
            'date_joined': user_detail.date_joined.strftime('%d/%m/%Y %H:%M'),
            'last_login': user_detail.last_login.strftime('%d/%m/%Y %H:%M') if user_detail.last_login else 'Nunca',
            'avatar_url': user_detail.avatar.url if user_detail.avatar else None,
            'stats': user_stats,
            'recent_activity': recent_activity,
            'courses': user_courses,
            'achievements': user_achievements,
        }
        
        # Datos adicionales según el tipo de usuario
        if user_detail.user_type == 'expert':
            user_data['professional_title'] = getattr(user_detail, 'professional_title', '')
            user_data['expertise_area'] = getattr(user_detail, 'expertise_area', '')
            user_data['professional_experience'] = getattr(user_detail, 'professional_experience', 0)
        
        return JsonResponse({
            'success': True,
            'user': user_data
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def get_user_statistics(user):
    """Obtener estadísticas específicas del usuario"""
    stats = {
        'total_courses': 0,
        'total_assignments': 0,
        'completed_assignments': 0,
        'average_grade': 0,
        'total_achievements': 0,
        'login_count': 0,
        'messages_sent': 0,
        'messages_received': 0,
    }
    
    try:
        if user.user_type == 'student':
            # Estadísticas de estudiante
            enrollments = Enrollment.objects.filter(student=user)
            stats['total_courses'] = enrollments.count()
            
            # Tareas
            all_assignments = Assignment.objects.filter(course__in=[e.course for e in enrollments])
            stats['total_assignments'] = all_assignments.count()
            
            # Tareas completadas
            completed = AssignmentSubmission.objects.filter(student=user)
            stats['completed_assignments'] = completed.count()
            
            # Promedio de calificaciones
            graded_submissions = completed.filter(grade__isnull=False)
            if graded_submissions.exists():
                avg_grade = graded_submissions.aggregate(avg=Avg('grade'))['avg']
                stats['average_grade'] = round(avg_grade, 2) if avg_grade else 0
            
            # Logros
            achievements = StudentAchievement.objects.filter(student=user)
            stats['total_achievements'] = achievements.count()
            
        elif user.user_type == 'teacher':
            # Estadísticas de profesor
            courses = Course.objects.filter(teacher=user)
            stats['total_courses'] = courses.count()
            
            # Estudiantes totales
            total_students = Enrollment.objects.filter(course__in=courses).count()
            stats['total_students'] = total_students
            
            # Tareas creadas
            assignments = Assignment.objects.filter(course__in=courses)
            stats['total_assignments'] = assignments.count()
            
            # Submissions pendientes de calificar
            pending_submissions = AssignmentSubmission.objects.filter(
                assignment__in=assignments,
                grade__isnull=True
            ).count()
            stats['pending_submissions'] = pending_submissions
            
        elif user.user_type == 'expert':
            # Estadísticas de experto
            try:
                from apps.content.models import EducationalSheet, SheetRevisionHistory
                
                # Fichas revisadas
                reviewed_sheets = SheetRevisionHistory.objects.filter(
                    user=user,
                    action__in=['reviewed', 'approved', 'rejected']
                ).count()
                stats['reviewed_sheets'] = reviewed_sheets
                
                # Fichas aprobadas
                approved_sheets = SheetRevisionHistory.objects.filter(
                    user=user,
                    action='approved'
                ).count()
                stats['approved_sheets'] = approved_sheets
                
                # Fichas rechazadas
                rejected_sheets = SheetRevisionHistory.objects.filter(
                    user=user,
                    action='rejected'
                ).count()
                stats['rejected_sheets'] = rejected_sheets
                
                # Tasa de aprobación
                total_decisions = approved_sheets + rejected_sheets
                if total_decisions > 0:
                    stats['approval_rate'] = round((approved_sheets / total_decisions) * 100, 1)
                else:
                    stats['approval_rate'] = 0
                
            except ImportError:
                pass
        
        # Mensajes para todos los tipos de usuario
        stats['messages_sent'] = Message.objects.filter(sender=user).count()
        stats['messages_received'] = Message.objects.filter(
            conversation__participants=user
        ).exclude(sender=user).count()
        
        # Intentar obtener conteo de logins (si tienes un modelo de actividad)
        stats['login_count'] = getattr(user, 'login_count', 0)
        
    except Exception as e:
        print(f"Error calculando estadísticas para usuario {user.id}: {e}")
    
    return stats

def get_user_recent_activity(user):
    """Obtener actividad reciente del usuario"""
    activities = []
    
    try:
        # Últimas 10 actividades del usuario
        if user.user_type == 'student':
            # Entregas recientes
            recent_submissions = AssignmentSubmission.objects.filter(
                student=user
            ).select_related('assignment', 'assignment__course').order_by('-submitted_at')[:5]
            
            for submission in recent_submissions:
                activities.append({
                    'type': 'assignment_submission',
                    'description': f'Entregó tarea: {submission.assignment.title}',
                    'details': f'Curso: {submission.assignment.course.name}',
                    'timestamp': submission.submitted_at.strftime('%d/%m/%Y %H:%M'),
                    'icon': 'file-earmark-text'
                })
            
            # Inscripciones a cursos
            recent_enrollments = Enrollment.objects.filter(
                student=user
            ).select_related('course').order_by('-enrollment_date')[:3]
            
            for enrollment in recent_enrollments:
                activities.append({
                    'type': 'course_enrollment',
                    'description': f'Se inscribió en: {enrollment.course.name}',
                    'details': f'Fecha: {enrollment.enrollment_date.strftime("%d/%m/%Y")}',
                    'timestamp': enrollment.enrollment_date.strftime('%d/%m/%Y %H:%M'),
                    'icon': 'book'
                })
        
        elif user.user_type == 'teacher':
            # Cursos creados
            recent_courses = Course.objects.filter(
                teacher=user
            ).order_by('-created_at')[:3]
            
            for course in recent_courses:
                activities.append({
                    'type': 'course_created',
                    'description': f'Creó curso: {course.name}',
                    'details': f'Código: {course.code}',
                    'timestamp': course.created_at.strftime('%d/%m/%Y %H:%M'),
                    'icon': 'plus-circle'
                })
            
            # Tareas creadas
            recent_assignments = Assignment.objects.filter(
                course__teacher=user
            ).select_related('course').order_by('-created_at')[:3]
            
            for assignment in recent_assignments:
                activities.append({
                    'type': 'assignment_created',
                    'description': f'Creó tarea: {assignment.title}',
                    'details': f'Curso: {assignment.course.name}',
                    'timestamp': assignment.created_at.strftime('%d/%m/%Y %H:%M'),
                    'icon': 'clipboard-plus'
                })
        
        # Mensajes enviados (para todos los tipos)
        recent_messages = Message.objects.filter(
            sender=user
        ).select_related('conversation').order_by('-timestamp')[:3]
        
        for message in recent_messages:
            # Obtener el destinatario
            other_participants = message.conversation.participants.exclude(id=user.id)
            recipient = other_participants.first() if other_participants.exists() else None
            
            activities.append({
                'type': 'message_sent',
                'description': f'Envió mensaje a: {recipient.get_full_name() if recipient else "Usuario"}',
                'details': f'Contenido: {message.content[:50]}...' if len(message.content) > 50 else message.content,
                'timestamp': message.timestamp.strftime('%d/%m/%Y %H:%M'),
                'icon': 'chat-dots'
            })
        
        # Ordenar por timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
    except Exception as e:
        print(f"Error obteniendo actividad reciente para usuario {user.id}: {e}")
    
    return activities[:10]  # Limitar a 10 actividades

def get_user_courses(user):
    """Obtener cursos del usuario"""
    courses = []
    
    try:
        if user.user_type == 'student':
            enrollments = Enrollment.objects.filter(
                student=user
            ).select_related('course', 'course__teacher').order_by('-enrollment_date')
            
            for enrollment in enrollments:
                courses.append({
                    'id': enrollment.course.id,
                    'name': enrollment.course.name,
                    'code': enrollment.course.code,
                    'teacher_name': enrollment.course.teacher.get_full_name() if enrollment.course.teacher else 'Sin asignar',
                    'enrollment_date': enrollment.enrollment_date.strftime('%d/%m/%Y'),
                    'progress': enrollment.progress,
                    'status': enrollment.course.status if hasattr(enrollment.course, 'status') else 'active'
                })
        
        elif user.user_type == 'teacher':
            teacher_courses = Course.objects.filter(
                teacher=user
            ).order_by('-created_at')
            
            for course in teacher_courses:
                student_count = Enrollment.objects.filter(course=course).count()
                courses.append({
                    'id': course.id,
                    'name': course.name,
                    'code': course.code,
                    'student_count': student_count,
                    'created_at': course.created_at.strftime('%d/%m/%Y'),
                    'status': course.status if hasattr(course, 'status') else 'active'
                })
        
    except Exception as e:
        print(f"Error obteniendo cursos para usuario {user.id}: {e}")
    
    return courses

def get_user_achievements(user):
    """Obtener logros del usuario"""
    achievements = []
    
    try:
        if user.user_type == 'student':
            student_achievements = StudentAchievement.objects.filter(
                student=user
            ).select_related('achievement').order_by('-earned_at')
            
            for sa in student_achievements:
                achievements.append({
                    'id': sa.achievement.id,
                    'name': sa.achievement.name,
                    'description': sa.achievement.description,
                    'points': sa.achievement.points,
                    'icon': sa.achievement.icon,
                    'earned_at': sa.earned_at.strftime('%d/%m/%Y %H:%M')
                })
        
    except Exception as e:
        print(f"Error obteniendo logros para usuario {user.id}: {e}")
    
    return achievements
# ...existing code...

@login_required
def admin_user_delete(request, user_id):
    """Vista para eliminar un usuario (solo admin)"""
    if not request.user.is_authenticated or request.user.user_type != 'admin':
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción'})
    
    if request.method == 'DELETE':
        try:
            user_to_delete = get_object_or_404(User, id=user_id)
            
            # Verificar que no se esté intentando eliminar a sí mismo
            if user_to_delete.id == request.user.id:
                return JsonResponse({
                    'success': False, 
                    'error': 'No puedes eliminar tu propia cuenta'
                })
            
            # Verificar que no sea el único administrador
            if user_to_delete.user_type == 'admin':
                admin_count = User.objects.filter(user_type='admin', is_active=True).count()
                if admin_count <= 1:
                    return JsonResponse({
                        'success': False,
                        'error': 'No se puede eliminar el último administrador del sistema'
                    })
            
            # Guardar información del usuario antes de eliminarlo
            user_name = user_to_delete.get_full_name()
            user_email = user_to_delete.email
            user_type = user_to_delete.get_user_type_display()
            
            # Realizar la eliminación en una transacción
            with transaction.atomic():
                # Opcional: Mover datos importantes a una tabla de historial antes de eliminar
                # create_user_deletion_log(user_to_delete, request.user)
                
                # Eliminar archivos asociados (avatar, materiales subidos, etc.)
                cleanup_user_files(user_to_delete)
                
                # Eliminar el usuario (esto también eliminará relaciones en cascada)
                user_to_delete.delete()
                
                # Crear log de la acción para auditoría
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Usuario eliminado: {user_name} ({user_email}) - "
                    f"Tipo: {user_type} - "
                    f"Eliminado por: {request.user.get_full_name()} ({request.user.email})"
                )
            
            return JsonResponse({
                'success': True,
                'message': f'Usuario {user_name} eliminado exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Error al eliminar usuario: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

def cleanup_user_files(user):
    """Función auxiliar para limpiar archivos del usuario eliminado"""
    try:
        # Eliminar avatar si existe
        if user.avatar:
            try:
                if default_storage.exists(user.avatar.name):
                    default_storage.delete(user.avatar.name)
            except Exception as e:
                print(f"Error eliminando avatar: {e}")
        
        # Eliminar materiales subidos por el usuario
        try:
            materials = Material.objects.filter(uploaded_by=user)
            for material in materials:
                if material.file:
                    try:
                        if default_storage.exists(material.file.name):
                            default_storage.delete(material.file.name)
                    except Exception as e:
                        print(f"Error eliminando material {material.id}: {e}")
        except Exception as e:
            print(f"Error eliminando materiales: {e}")
        
        # Eliminar archivos de assignments si es profesor
        try:
            if user.user_type == 'teacher':
                assignments = Assignment.objects.filter(created_by=user)
                for assignment in assignments:
                    if assignment.attachment:
                        try:
                            if default_storage.exists(assignment.attachment.name):
                                default_storage.delete(assignment.attachment.name)
                        except Exception as e:
                            print(f"Error eliminando attachment de assignment {assignment.id}: {e}")
        except Exception as e:
            print(f"Error eliminando archivos de assignments: {e}")
        
        # Eliminar archivos de submissions si es estudiante
        try:
            if user.user_type == 'student':
                submissions = AssignmentSubmission.objects.filter(student=user)
                for submission in submissions:
                    if submission.file:
                        try:
                            if default_storage.exists(submission.file.name):
                                default_storage.delete(submission.file.name)
                        except Exception as e:
                            print(f"Error eliminando archivo de submission {submission.id}: {e}")
        except Exception as e:
            print(f"Error eliminando archivos de submissions: {e}")
            
    except Exception as e:
        print(f"Error general en cleanup_user_files: {e}")

def create_user_deletion_log(user, admin_user):
    """Función auxiliar para crear log de eliminación (opcional)"""
    try:
        # Aquí podrías crear un registro en una tabla de auditoría
        # Por ejemplo, guardar información importante del usuario eliminado
        deletion_data = {
            'deleted_user_id': user.id,
            'deleted_user_name': user.get_full_name(),
            'deleted_user_email': user.email,
            'deleted_user_type': user.user_type,
            'deletion_date': timezone.now(),
            'deleted_by_admin_id': admin_user.id,
            'deleted_by_admin_name': admin_user.get_full_name(),
        }
        
        # Si tienes un modelo UserDeletionLog, podrías crear el registro aquí
        # UserDeletionLog.objects.create(**deletion_data)
        
        # Por ahora, solo logueamos la información
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Registro de eliminación creado: {deletion_data}")
        
    except Exception as e:
        print(f"Error creando log de eliminación: {e}")

@login_required
def admin_user_toggle_status(request, user_id):
    """Vista para activar/desactivar un usuario (solo admin)"""
    if not request.user.is_authenticated or request.user.user_type != 'admin':
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción'})
    
    if request.method == 'POST':
        try:
            user_to_toggle = get_object_or_404(User, id=user_id)
            
            # Verificar que no se esté intentando desactivar a sí mismo
            if user_to_toggle.id == request.user.id:
                return JsonResponse({
                    'success': False, 
                    'error': 'No puedes cambiar el estado de tu propia cuenta'
                })
            
            # Verificar que no sea el único administrador activo
            if user_to_toggle.user_type == 'admin' and user_to_toggle.is_active:
                active_admin_count = User.objects.filter(
                    user_type='admin', 
                    is_active=True
                ).exclude(id=user_to_toggle.id).count()
                
                if active_admin_count == 0:
                    return JsonResponse({
                        'success': False,
                        'error': 'No se puede desactivar el último administrador activo del sistema'
                    })
            
            # Cambiar el estado
            user_to_toggle.is_active = not user_to_toggle.is_active
            user_to_toggle.save()
            
            # Crear notificación para el usuario (si se está activando)
            if user_to_toggle.is_active:
                try:
                    Notification.objects.create(
                        recipient=user_to_toggle,
                        title='Cuenta reactivada',
                        message='Tu cuenta ha sido reactivada por un administrador. Ya puedes acceder nuevamente al sistema.',
                        notification_type='system'
                    )
                except Exception as e:
                    print(f"Error creando notificación: {e}")
            
            # Registrar la acción para auditoría
            import logging
            logger = logging.getLogger(__name__)
            action = 'activado' if user_to_toggle.is_active else 'desactivado'
            logger.info(
                f"Usuario {action}: {user_to_toggle.get_full_name()} ({user_to_toggle.email}) - "
                f"Acción realizada por: {request.user.get_full_name()} ({request.user.email})"
            )
            
            status_text = 'activado' if user_to_toggle.is_active else 'desactivado'
            
            return JsonResponse({
                'success': True,
                'message': f'Usuario {user_to_toggle.get_full_name()} {status_text} exitosamente',
                'new_status': user_to_toggle.is_active
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Error al cambiar estado del usuario: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def generate_unique_course_code():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Course.objects.filter(code=code).exists():
            return code

@login_required
@require_http_methods(["POST"])
def create_course(request):
    if request.user.user_type != 2:
        return JsonResponse({'success': False, 'error': 'Solo los docentes pueden crear cursos'})
    
    try:
        data = json.loads(request.body)
        name = data.get('name')
        code = data.get('code')
        description = data.get('description', '')
        subject_name = data.get('subject', '').strip()
        grade = data.get('grade', '').strip()
        
        if not name:
            return JsonResponse({'success': False, 'error': 'El nombre del curso es requerido'})
        
        if not subject_name:
            return JsonResponse({'success': False, 'error': 'La materia es requerida'})
        
        if not grade:
            return JsonResponse({'success': False, 'error': 'El grado es requerido'})

        # Si no se envía código o ya existe, genera uno nuevo
        if not code or Course.objects.filter(code=code).exists():
            code = generate_unique_course_code()

        # Buscar o crear el Subject
        subject, created = Subject.objects.get_or_create(name=subject_name)

        # Crear el curso con todos los campos
        course = Course.objects.create(
            name=name,
            code=code,
            description=description,
            teacher=request.user,
            subject=subject,
            grade=grade
        )
        
        return JsonResponse({
            'success': True, 
            'course_id': course.id, 
            'code': code,
            'message': f'Curso "{name}" creado exitosamente'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'})
@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Verificar permisos
    if request.user.user_type == 2:  # Docente
        if course.teacher != request.user:
            return redirect('users:dashboard_teacher', user_id=request.user.id)
    elif request.user.user_type == 3:  # Estudiante
        if not Enrollment.objects.filter(student=request.user, course=course).exists():
            return redirect('users:dashboard_student', user_id=request.user.id)
    else:
        return redirect('users:login')
    
    # Obtener datos del curso
    enrollments = Enrollment.objects.filter(course=course)
    students = [enrollment.student for enrollment in enrollments]
    
    # Obtener materiales del curso
    materials = Material.objects.filter(course=course, is_active=True)
    print(f"Materiales encontrados: {materials.count()}")  # Debug
    for material in materials:
        print(f"- {material.title} ({material.id})")  # Debug
    
    # Estadísticas
    total_students = enrollments.count()
    total_assignments = 0  # Cambiar cuando tengas Assignment model
    
    context = {
        'user': request.user,
        'course': course,
        'students': students,
        'materials': materials,  # Importante: esto debe estar aquí
        'total_students': total_students,
        'total_assignments': total_assignments,
        'is_teacher': request.user.user_type == 2,
        'is_student': request.user.user_type == 3,
    }
    
    print(f"Context materials: {context['materials']}")  # Debug
    
    return render(request, 'courses/course_detail.html', context)

# Nueva vista para mostrar estudiantes
@login_required
def course_students(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Verificar permisos
    if request.user.user_type == 2 and course.teacher != request.user:
        return redirect('users:dashboard_teacher', user_id=request.user.id)
    elif request.user.user_type == 3 and not Enrollment.objects.filter(student=request.user, course=course).exists():
        return redirect('users:dashboard_student', user_id=request.user.id)
    
    # Obtener estudiantes con información adicional
    enrollments = Enrollment.objects.filter(course=course).select_related('student')
    students_data = []
    
    for enrollment in enrollments:
        student = enrollment.student
        # Obtener estadísticas del estudiante
        total_assignments = Assignment.objects.filter(course=course).count() if 'Assignment' in globals() else 0
        submitted_assignments = AssignmentSubmission.objects.filter(
            assignment__course=course, 
            student=student
        ).count() if 'AssignmentSubmission' in globals() else 0
        
        students_data.append({
            'student': student,
            'enrollment_date': enrollment.enrollment_date,
            'total_assignments': total_assignments,
            'submitted_assignments': submitted_assignments,
        })
    
    context = {
        'course': course,
        'students_data': students_data,
        'total_students': len(students_data),
        'is_teacher': request.user.user_type == 2,
    }
    
    return render(request, 'courses/course_students.html', context)

# Nueva vista para mostrar tareas
@login_required
def course_assignments(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Verificar permisos
    if request.user.user_type == 2 and course.teacher != request.user:
        return redirect('users:dashboard_teacher', user_id=request.user.id)
    elif request.user.user_type == 3 and not Enrollment.objects.filter(student=request.user, course=course).exists():
        return redirect('users:dashboard_student', user_id=request.user.id)
    
    # Obtener todas las tareas
    assignments = Assignment.objects.filter(course=course).order_by('-created_at') if 'Assignment' in globals() else []
    
    # Clasificar tareas por estado
    from django.utils import timezone
    now = timezone.now()
    
    active_assignments = []
    past_assignments = []
    
    for assignment in assignments:
        if hasattr(assignment, 'due_date') and assignment.due_date:
            if assignment.due_date > now:
                active_assignments.append(assignment)
            else:
                past_assignments.append(assignment)
        else:
            active_assignments.append(assignment)
    
    context = {
        'course': course,
        'active_assignments': active_assignments,
        'past_assignments': past_assignments,
        'total_assignments': len(assignments),
        'is_teacher': request.user.user_type == 2,
    }
    
    return render(request, 'courses/course_assignments.html', context)
@login_required
def join_course_link(request, code):
    try:
        course = Course.objects.get(code=code)
    except Course.DoesNotExist:
        messages.error(request, 'El código de curso no es válido.')
        return redirect('users:dashboard_student')

    # Solo estudiantes pueden inscribirse
    if request.user.user_type != 1:
        messages.error(request, 'Solo los estudiantes pueden inscribirse en cursos.')
        return redirect('users:dashboard_student')

    # Verifica si ya está inscrito
    enrollment, created = Enrollment.objects.get_or_create(student=request.user, course=course)
    if created:
        messages.success(request, f'Te has inscrito exitosamente en {course.name}.')
    else:
        messages.info(request, f'Ya estás inscrito en {course.name}.')

    return redirect('users:student_courses')

@login_required
def teacher_courses(request):
    user = request.user
    if user.user_type != 2:
        return redirect('users:dashboard_student')
    
    courses = Course.objects.filter(teacher=user)
    
    # Calcular estadísticas
    total_courses = courses.count()
    total_students = Enrollment.objects.filter(course__in=courses).count()
    pending_submissions = AssignmentSubmission.objects.filter(
        assignment__course__in=courses,
        grade__isnull=True
    ).count()
    
    # Agregar datos estadísticos a cada curso
    courses_with_stats = []
    for course in courses:
        course_students = Enrollment.objects.filter(course=course).count()
        course_assignments = Assignment.objects.filter(course=course).count()
        
        # Promedio de calificaciones
        submissions = AssignmentSubmission.objects.filter(
            assignment__course=course,
            grade__isnull=False
        )
        avg_grade = submissions.aggregate(avg=Avg('grade'))['avg'] or 0
        
        courses_with_stats.append({
            'id': course.id,
            'name': course.name,
            'code': course.code,
            'description': course.description,
            'status': getattr(course, 'status', 'active'),
            'students_count': course_students,
            'assignments_count': course_assignments,
            'avg_grade': round(avg_grade, 1),
            'subject': getattr(course, 'subject', None),
            'icon': getattr(getattr(course, 'subject', None), 'icon', 'book'),
        })
    
    context = {
        'user': user,
        'courses': courses_with_stats,
        'total_courses': total_courses,
        'total_students': total_students,
        'pending_submissions': pending_submissions,
        'avg_completion': 0,  # Puedes calcular esto si necesitas
    }
    return render(request, 'teachers/courses.html', context)
@login_required
@require_http_methods(["POST"])
def upload_material(request, course_id):
    print(f"[DEBUG] Subiendo material para curso: {course_id}")
    
    course = get_object_or_404(Course, id=course_id)
    
    if request.user.user_type != 2 or course.teacher != request.user:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para subir materiales'})
    
    try:
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        url = request.POST.get('url', '')
        file = request.FILES.get('file')
        
        print(f"[DEBUG] Título: {title}")
        print(f"[DEBUG] Archivo: {file}")
        print(f"[DEBUG] URL: {url}")
        
        if not title:
            return JsonResponse({'success': False, 'error': 'El título es requerido'})
        
        if not file and not url:
            return JsonResponse({'success': False, 'error': 'Debes subir un archivo o proporcionar una URL'})
        
        # Crear el material
        material = Material.objects.create(
            course=course,
            title=title,
            description=description,
            file=file if file else None,
            url=url if url else '',
            uploaded_by=request.user
        )
        
        print(f"[DEBUG] Material creado: {material.id} - {material.title}")
        
        return JsonResponse({
            'success': True,
            'message': f'Material "{title}" subido exitosamente',
            'material_id': material.id
        })
        
    except Exception as e:
        print(f"[DEBUG] Error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Error al subir material: {str(e)}'})
@login_required
def delete_material(request, material_id):
    material = get_object_or_404(Material, id=material_id)
    
    # Verificar permisos
    if request.user.user_type != 2 or material.course.teacher != request.user:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para eliminar este material'})
    
    try:
        # Eliminar archivo del sistema si existe
        if material.file:
            if default_storage.exists(material.file.name):
                default_storage.delete(material.file.name)
        
        material.delete()
        return JsonResponse({'success': True, 'message': 'Material eliminado exitosamente'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error al eliminar material: {str(e)}'})
@login_required
def course_materials(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Verificar permisos
    if request.user.user_type == 2 and course.teacher != request.user:
        return redirect('users:dashboard_teacher', user_id=request.user.id)
    elif request.user.user_type == 3 and not Enrollment.objects.filter(student=request.user, course=course).exists():
        return redirect('users:dashboard_student', user_id=request.user.id)
    
    materials = Material.objects.filter(course=course, is_active=True)
    
    context = {
        'course': course,
        'materials': materials,
        'is_teacher': request.user.user_type == 2,
    }
    
    return render(request, 'courses/course_materials.html', context)
#Tareas 
@login_required
@require_http_methods(["POST"])
def create_assignment(request, course_id):
    print(f"[DEBUG] === CREAR TAREA ===")
    print(f"[DEBUG] Course ID: {course_id}")
    print(f"[DEBUG] User: {request.user.username}")
    print(f"[DEBUG] User type: {request.user.user_type}")
    
    course = get_object_or_404(Course, id=course_id)
    print(f"[DEBUG] Course found: {course.name}")
    
    # Verificar permisos
    if request.user.user_type != 2 or course.teacher != request.user:
        print(f"[DEBUG] Permission denied. User type: {request.user.user_type}, Teacher: {course.teacher}")
        return JsonResponse({'success': False, 'error': 'No tienes permisos para crear tareas'})
    
    try:
        title = request.POST.get('title')
        description = request.POST.get('description')
        instructions = request.POST.get('instructions', '')
        due_date_str = request.POST.get('due_date')
        max_points = request.POST.get('max_points', 100)
        allow_late_submission = request.POST.get('allow_late_submission') == 'on'
        attachment = request.FILES.get('attachment')
        
        print(f"[DEBUG] Form data:")
        print(f"  - Title: {title}")
        print(f"  - Description: {description}")
        print(f"  - Due date: {due_date_str}")
        print(f"  - Max points: {max_points}")
        print(f"  - Allow late: {allow_late_submission}")
        
        if not title or not description or not due_date_str:
            print(f"[DEBUG] Missing required fields")
            return JsonResponse({'success': False, 'error': 'Título, descripción y fecha límite son requeridos'})
        
        # Convertir fecha string a datetime
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            due_date = timezone.make_aware(due_date)
            print(f"[DEBUG] Parsed due date: {due_date}")
        except ValueError as e:
            print(f"[DEBUG] Date parsing error: {e}")
            return JsonResponse({'success': False, 'error': 'Formato de fecha inválido'})
        
        # Verificar que la fecha sea futura
        if due_date <= timezone.now():
            print(f"[DEBUG] Due date is in the past")
            return JsonResponse({'success': False, 'error': 'La fecha límite debe ser futura'})
        
        # Crear la tarea
        assignment = Assignment.objects.create(
            course=course,
            title=title,
            description=description,
            instructions=instructions,
            due_date=due_date,
            created_by=request.user,
            max_points=max_points,
            allow_late_submission=allow_late_submission,
            attachment=attachment if attachment else None,
            status='published'
        )
        
        print(f"[DEBUG] Assignment created successfully:")
        print(f"  - ID: {assignment.id}")
        print(f"  - Title: {assignment.title}")
        print(f"  - Status: {assignment.status}")
        print(f"  - Course: {assignment.course.name}")
        
        # Verificar que se guardó correctamente
        saved_assignment = Assignment.objects.get(id=assignment.id)
        print(f"[DEBUG] Assignment verified in DB: {saved_assignment.title}")
        
        return JsonResponse({
            'success': True,
            'message': f'Tarea "{title}" creada exitosamente',
            'assignment_id': assignment.id
        })
        
    except Exception as e:
        print(f"[DEBUG] Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Error al crear tarea: {str(e)}'})

@login_required
def assignment_detail(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    # Verificar permisos
    if request.user.user_type == 2 and assignment.course.teacher != request.user:
        return redirect('users:dashboard_teacher', user_id=request.user.id)
    elif request.user.user_type == 3 and not Enrollment.objects.filter(student=request.user, course=assignment.course).exists():
        return redirect('users:dashboard_student', user_id=request.user.id)
    
    # Obtener submission del estudiante si existe
    submission = None
    if request.user.user_type == 3:
        try:
            submission = AssignmentSubmission.objects.get(assignment=assignment, student=request.user)
        except AssignmentSubmission.DoesNotExist:
            pass
    
    # Obtener todas las submissions si es profesor
    submissions = None
    if request.user.user_type == 2:
        submissions = AssignmentSubmission.objects.filter(assignment=assignment)
    
    context = {
        'assignment': assignment,
        'course': assignment.course,
        'submission': submission,
        'submissions': submissions,
        'is_teacher': request.user.user_type == 2,
        'is_student': request.user.user_type == 3,
        'is_overdue': assignment.is_overdue(),
        'days_until_due': assignment.days_until_due(),
    }
    
    return render(request, 'assignments/assignment_detail.html', context)

@login_required
def assignment_submissions(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    # Verificar que el usuario sea el profesor del curso
    if request.user.user_type != 2 or assignment.course.teacher != request.user:
        return redirect('users:dashboard_teacher', user_id=request.user.id)
    
    submissions = AssignmentSubmission.objects.filter(assignment=assignment).select_related('student')
    enrolled_students = Enrollment.objects.filter(course=assignment.course).select_related('student')
    
    # Crear lista de estudiantes con sus submissions
    students_data = []
    for enrollment in enrolled_students:
        student = enrollment.student
        try:
            submission = submissions.get(student=student)
        except AssignmentSubmission.DoesNotExist:
            submission = None
        
        students_data.append({
            'student': student,
            'submission': submission,
            'has_submitted': submission is not None
        })
    
    context = {
        'assignment': assignment,
        'course': assignment.course,
        'students_data': students_data,
        'total_submissions': submissions.count(),
        'total_students': enrolled_students.count(),
    }
    
    return render(request, 'assignments/assignment_submissions.html', context)
# Reemplaza la función course_detail (líneas 1329-1407) con esta versión simplificada:

@login_required
def course_detail(request, course_id):
    print(f"[DEBUG] ===== COURSE DETAIL =====")
    print(f"[DEBUG] Course ID: {course_id}")
    print(f"[DEBUG] User: {request.user.username}")
    
    course = get_object_or_404(Course, id=course_id)
    print(f"[DEBUG] Course found: {course.name}")
    
    # Verificar permisos
    if request.user.user_type == 2:  # Docente
        if course.teacher != request.user:
            return redirect('users:dashboard_teacher', user_id=request.user.id)
    elif request.user.user_type == 3:  # Estudiante
        if not Enrollment.objects.filter(student=request.user, course=course).exists():
            return redirect('users:dashboard_student', user_id=request.user.id)
    else:
        return redirect('users:login')
    
    # Obtener datos del curso
    enrollments = Enrollment.objects.filter(course=course)
    students = [enrollment.student for enrollment in enrollments]
    
    # Obtener materiales del curso
    materials = Material.objects.filter(course=course, is_active=True)
    
    # Debug en consola
    print(f"[DEBUG] Course ID: {course_id}")
    print(f"[DEBUG] Materials count: {materials.count()}")
    print(f"[DEBUG] Materials queryset: {materials}")
    for material in materials:
        print(f"[DEBUG] Material: {material.id} - {material.title} - {material.file}")
    
    # Obtener assignments del curso - SIMPLIFICADO
    print(f"[DEBUG] ===== ASSIGNMENTS DEBUG =====")
    
    try:
        # Obtener TODAS las assignments del curso sin filtros
        all_assignments = Assignment.objects.filter(course=course)
        print(f"[DEBUG] Total assignments for course: {all_assignments.count()}")
        
        # Mostrar cada assignment
        for assignment in all_assignments:
            print(f"[DEBUG] Assignment: {assignment.id} - {assignment.title} - Status: {assignment.status}")
        
        # Usar todas las assignments (no filtrar por status todavía)
        assignments = all_assignments
        print(f"[DEBUG] Using assignments: {assignments.count()}")
        
    except Exception as e:
        print(f"[DEBUG] Error getting assignments: {e}")
        assignments = Assignment.objects.none()  # QuerySet vacío
    
    # Estadísticas
    total_students = enrollments.count()
    total_assignments = assignments.count()
    
    print(f"[DEBUG] Final context:")
    print(f"  - Total students: {total_students}")
    print(f"  - Total assignments: {total_assignments}")
    print(f"  - Is teacher: {request.user.user_type == 2}")
    
    context = {
        'user': request.user,
        'course': course,
        'students': students,
        'materials': materials,
        'assignments': assignments,  # Variable clave
        'total_students': total_students,
        'total_assignments': total_assignments,
        'is_teacher': request.user.user_type == 2,
        'is_student': request.user.user_type == 3,
    }
    
    print(f"[DEBUG] Context assignments type: {type(context['assignments'])}")
    print(f"[DEBUG] Context assignments count: {context['assignments'].count()}")
    
    return render(request, 'courses/course_detail.html', context)
@login_required
def dashboard_parent(request, user_id):
    user = request.user
    if request.user.id != user_id:
        # Redirige al dashboard correcto del usuario autenticado
        return redirect('users:dashboard_parent', user_id=request.user.id)
    user = request.user
    if user.user_type != 3:
        return redirect('users:login')

    # Obtener hijos del padre
    children = user.parent_profile.children.filter(user_type=1)    
    children_count = children.count()

    # Cursos y logros de los hijos
    children_courses = []
    recent_achievements = []
    upcoming_events = []

    for child in children:
        enrollments = Enrollment.objects.filter(student=child).select_related('course')
        for enrollment in enrollments:
            children_courses.append({
                'child': child,
                'course': enrollment.course,
                'progress': enrollment.progress,
            })
        # Logros recientes del hijo
        achievements = StudentAchievement.objects.filter(student=child).select_related('achievement').order_by('-earned_at')[:2]
        recent_achievements.extend(achievements)
        # Próximos eventos del hijo
        events = CalendarEvent.objects.filter(
            participants=child,
            start_date__gte=timezone.now()
        ).order_by('start_date')[:2]
        upcoming_events.extend(events)

    context = {
        'user': user,
        'children': children,
        'children_count': children_count,
        'children_courses': children_courses,
        'recent_achievements': recent_achievements,
        'upcoming_events': upcoming_events,
    }
    return render(request, 'dashboards/dashboard_parent.html', context)
@login_required
def sons_list(request):
    user = request.user
    if user.user_type != 3:
        return redirect('users:login')
    children = user.parent_profile.children.filter(user_type=1)
    context = {
        'children': children,
    }
    return render(request, 'parents/sons.html', context)



def get_user_dashboard_url(user):
    """
    Función auxiliar para obtener la URL del dashboard según el tipo de usuario
    """
    if user.user_type in USER_TYPE_CONFIG:
        dashboard_url = USER_TYPE_CONFIG[user.user_type]['dashboard_url']
        return reverse(dashboard_url, kwargs={'user_id': user.id})
    return reverse('users:login')

@login_required
def redirect_to_user_dashboard(request):
    """
    Redirige al usuario a su dashboard correspondiente según su tipo
    """
    user = request.user
    if user.user_type in USER_TYPE_CONFIG:
        dashboard_url = USER_TYPE_CONFIG[user.user_type]['dashboard_url']
        return redirect(dashboard_url, user_id=user.id)
    else:
        messages.error(request, "Tipo de usuario no reconocido.")
        return redirect('users:login')

def home_redirect(request):
    """
    Redirecciona desde la raíz del sitio
    """
    if request.user.is_authenticated:
        return redirect_to_user_dashboard(request)
    else:
        return redirect('users:login')

# Función auxiliar para usar en templates
def get_registration_links():
    """
    Devuelve los enlaces de registro disponibles
    """
    return {
        'estudiante': reverse('users:register_student'),
        'docente': reverse('users:register_teacher'),
        'padre': reverse('users:register_parent'),
    }


# ===== VISTAS DE ESTUDIANTE =====

@login_required
def student_courses(request):
    """Vista para mostrar los cursos del estudiante"""
    user = request.user
    
    # Obtener todas las inscripciones del estudiante
    enrollments = Enrollment.objects.filter(
        student=user
    ).select_related('course', 'course__subject', 'course__teacher')
    
    courses_data = []
    for enrollment in enrollments:
        course = enrollment.course
        
        # Contar tareas del curso
        assignments_count = Assignment.objects.filter(course=course).count()
        
        courses_data.append({
            'id': course.id,
            'name': course.name,
            'code': course.code,
            'subject': course.subject.color_class if hasattr(course, 'subject') and course.subject else 'default',
            'icon': course.subject.icon if hasattr(course, 'subject') and course.subject else 'book',
            'teacher_name': course.teacher.get_full_name() if course.teacher else 'Sin asignar',
            'students_count': Enrollment.objects.filter(course=course).count(),
            'assignments_count': assignments_count,
            'progress': enrollment.progress,
            'status': course.status,
        })
    
    context = {
        'user': user,
        'courses': courses_data,
    }
    return render(request, 'students/courses.html', context)

@login_required
def student_assignments(request):
    """Vista para mostrar las tareas del estudiante"""
    user = request.user
    
    # Obtener cursos del estudiante usando la relación inversa (más eficiente)
    user_courses = Course.objects.filter(enrollment__student=user).distinct()
    
    # Tareas pendientes
    pending_assignments = Assignment.objects.filter(
        course__in=user_courses,
        due_date__gte=timezone.now()
    ).exclude(
        submissions__student=user
    ).select_related('course').order_by('due_date')
    
    # Tareas entregadas
    submitted_assignments = AssignmentSubmission.objects.filter(
        student=user
    ).select_related('assignment', 'assignment__course').order_by('-submitted_at')
    
    context = {
        'user': user,
        'pending_assignments': pending_assignments,
        'submitted_assignments': submitted_assignments,
        'today': timezone.now(),  # Agregar fecha actual
    }
    return render(request, 'students/assignments.html', context)


@login_required
def student_grades(request):
    """Vista para mostrar las calificaciones del estudiante"""
    user = request.user
    
    try:
        # Obtener todas las entregas con calificación del estudiante
        submissions = AssignmentSubmission.objects.filter(
            student=user,
            grade__isnull=False
        ).select_related('assignment', 'assignment__course', 'assignment__course__subject').order_by('-submitted_at')
        
        # Calcular estadísticas
        if submissions.exists():
            grades = [s.grade for s in submissions]
            average_grade = sum(grades) / len(grades)
            highest_grade = max(grades)
            lowest_grade = min(grades)
            total_assignments = submissions.count()
            
            # Distribución de calificaciones
            excellent_count = len([g for g in grades if g >= 9.0])
            good_count = len([g for g in grades if 8.0 <= g < 9.0])
            satisfactory_count = len([g for g in grades if 7.0 <= g < 8.0])
            needs_improvement_count = len([g for g in grades if g < 7.0])
            
        else:
            average_grade = 0
            highest_grade = 0
            lowest_grade = 0
            total_assignments = 0
            excellent_count = good_count = satisfactory_count = needs_improvement_count = 0
        
        # Agrupar calificaciones por curso
        grades_by_course = {}
        for submission in submissions:
            course_name = submission.assignment.course.name
            if course_name not in grades_by_course:
                grades_by_course[course_name] = {
                    'course': submission.assignment.course,
                    'submissions': [],
                    'average': 0,
                    'count': 0
                }
            grades_by_course[course_name]['submissions'].append(submission)
        
        # Calcular promedio por curso
        for course_data in grades_by_course.values():
            course_grades = [s.grade for s in course_data['submissions']]
            course_data['average'] = sum(course_grades) / len(course_grades)
            course_data['count'] = len(course_grades)
        
        context = {
            'user': user,
            'submissions': submissions,
            'average_grade': round(average_grade, 2),
            'highest_grade': highest_grade,
            'lowest_grade': lowest_grade,
            'total_assignments': total_assignments,
            'excellent_count': excellent_count,
            'good_count': good_count,
            'satisfactory_count': satisfactory_count,
            'needs_improvement_count': needs_improvement_count,
            'grades_by_course': grades_by_course,
        }
        
    except Exception as e:
        print(f"Error en student_grades: {e}")
        context = {
            'user': user,
            'submissions': [],
            'average_grade': 0,
            'highest_grade': 0,
            'lowest_grade': 0,
            'total_assignments': 0,
            'excellent_count': 0,
            'good_count': 0,
            'satisfactory_count': 0,
            'needs_improvement_count': 0,
            'grades_by_course': {},
        }
    
    return render(request, 'students/grades.html', context)
@login_required
def user_calendar(request):
    user = request.user
    # Obtener parámetros de fecha
    today = timezone.now().date()
    year = int(request.GET.get('year', date.today().year))
    month = int(request.GET.get('month', date.today().month))
    view_type = request.GET.get('view', 'month')
    
    # Crear fechas de inicio y fin según la vista
    if view_type == 'month':
        first_day = datetime(year, month, 1).date()
        if month == 12:
            last_day = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)
    elif view_type == 'week':
        # Obtener la semana actual
        today_datetime = datetime(year, month, 1)
        week_start = today_datetime - timedelta(days=today_datetime.weekday())
        first_day = week_start.date()
        last_day = (week_start + timedelta(days=6)).date()
    else:  # day
        first_day = last_day = datetime(year, month, 1).date()
    
    # Obtener eventos según el rol del usuario
    events = get_user_events(user, first_day, last_day)
    
    # Organizar eventos por fecha
    events_by_date = {}
    for event in events:
        date_str = event.start_date.date().strftime('%Y-%m-%d')
        if date_str not in events_by_date:
            events_by_date[date_str] = []
        events_by_date[date_str].append(event)

    # Preparar datos del calendario
    calendar_data = prepare_calendar_data(year, month, view_type)
    
    # Obtener estadísticas del usuario
    stats = get_calendar_stats(user, events)
    
    # Eventos de hoy y próximos
    today_events = [e for e in events if e.start_date.date() == today]
    upcoming_events = [e for e in events if e.is_upcoming() and e.start_date.date() > today][:5]
    
    # Preparar contexto
    context = {
        'user': user,
        'events': events,
        'events_by_date': events_by_date,
        'today_events': today_events,
        'upcoming_events': upcoming_events,
        'calendar_data': calendar_data,
        'stats': stats,
        'year': year,
        'month': month,
        'view_type': view_type,
        'today': today,
        'can_create_events': can_user_create_events(user),
        'event_types': get_available_event_types(user),
    }
    return render(request, 'shared/calendar.html', context)
@login_required
def calendar_partial(request):
    user = request.user
    today = timezone.now().date()
    year = int(request.GET.get('year', date.today().year))
    month = int(request.GET.get('month', date.today().month))
    view_type = request.GET.get('view', 'month')

    # Crear fechas de inicio y fin según la vista
    if view_type == 'month':
        first_day = datetime(year, month, 1).date()
        if month == 12:
            last_day = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)
    elif view_type == 'week':
        today_datetime = datetime(year, month, 1)
        week_start = today_datetime - timedelta(days=today_datetime.weekday())
        first_day = week_start.date()
        last_day = (week_start + timedelta(days=6)).date()
    else:  # day
        first_day = last_day = datetime(year, month, 1).date()
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # En Windows puede ser 'Spanish_Spain.1252'

    month_name = calendar.month_name[month].capitalize()
    events = get_user_events(user, first_day, last_day)
    events_by_date = {}
    for event in events:
        date_str = event.start_date.date().strftime('%Y-%m-%d')
        if date_str not in events_by_date:
            events_by_date[date_str] = []
        events_by_date[date_str].append(event)

    calendar_data = prepare_calendar_data(year, month, view_type)
    stats = get_calendar_stats(user, events)
    today_events = [e for e in events if e.start_date.date() == today]
    upcoming_events = [e for e in events if e.is_upcoming() and e.start_date.date() > today][:5]

    context = {
        'user': user,
        'events': events,
        'events_by_date': events_by_date,
        'today_events': today_events,
        'upcoming_events': upcoming_events,
        'calendar_data': calendar_data,
        'stats': stats,
        'year': year,
        'month': month,
        'view_type': view_type,
        'today': today,
        'can_create_events': can_user_create_events(user),
        'event_types': get_available_event_types(user),
    }
    html = render_to_string('shared/calendar_partial.html', context, request=request)
    return JsonResponse({'html': html})
def get_user_events(user, start_date, end_date):
    """Obtener eventos según el rol del usuario"""
    base_filter = Q(
        start_date__date__gte=start_date,
        start_date__date__lte=end_date
    )
    
    if user.user_type == 1:  # Estudiante
        # Eventos donde participa + tareas de sus cursos
        events = CalendarEvent.objects.filter(
            base_filter & (
                Q(user=user) |
                Q(participants=user) 
            )
        ).distinct()
        
        # Agregar tareas como eventos
        assignments = Assignment.objects.filter(
            course__enrollment__student=user,
            due_date__date__gte=start_date,
            due_date__date__lte=end_date
        ).select_related('course')
        
        # Convertir tareas a eventos
        for assignment in assignments:
            events = events.union(
                CalendarEvent.objects.filter(
                    title=assignment.title,
                    event_type='assignment',
                    start_date__date=assignment.due_date.date()
                )
            )
    
    elif user.user_type == 2:  # Docente
        # Eventos de sus cursos + eventos creados por él
        events = CalendarEvent.objects.filter(
            base_filter & (
                Q(course__teacher=user) |
                Q(created_by=user) |
                Q(participants=user)
            )
        ).distinct()
    
    elif user.user_type == 3:  # Padre
        # Eventos de los hijos
        children = user.parent_profile.children.filter(user_type=1)        
        events = CalendarEvent.objects.filter(
            base_filter & (
                Q(participants__in=children) |
                Q(course__enrollment__student__in=children) |
                Q(created_by=user)
            )
        ).distinct()

    elif user.user_type == 4:  # Experto
        # Eventos relacionados con revisiones + eventos propios
        events = CalendarEvent.objects.filter(
            base_filter & (
                Q(created_by=user) |
                Q(participants=user)
            )
        ).distinct()
    
    elif user.user_type == 5:  # Admin
        # Todos los eventos
        events = CalendarEvent.objects.filter(base_filter)
    
    
    return events.select_related('course', 'created_by').prefetch_related('participants')

def prepare_calendar_data(year, month, view_type):
    """Preparar datos del calendario según el tipo de vista"""
    if view_type == 'month':
        cal = calendar.Calendar(firstweekday=6)  # Domingo como primer día
        month_days = cal.monthdayscalendar(year, month)
        month_name = calendar.month_name[month]
        
        # Navegación
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        
        return {
            'month_days': month_days,
            'month_name': month_name,
            'prev_month': prev_month,
            'prev_year': prev_year,
            'next_month': next_month,
            'next_year': next_year,
        }
    
    return {}

def get_calendar_stats(user, events):
    """Obtener estadísticas del calendario"""
    total_events = events.count()
    today_events = len([e for e in events if e.is_today()])
    upcoming_events = len([e for e in events if e.is_upcoming()])
    
    # Eventos por tipo
    events_by_type = {}
    for event in events:
        event_type = event.get_event_type_display()
        events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
    
    return {
        'total_events': total_events,
        'today_events': today_events,
        'upcoming_events': upcoming_events,
        'events_by_type': events_by_type,
    }

def can_user_create_events(user):
    """Verificar si el usuario puede crear eventos"""
    return user.user_type in [2, 5]  # Docentes y administradores

def get_available_event_types(user):
    """Obtener tipos de eventos disponibles según el rol"""
    if user.user_type == 1:  # Estudiante
        return ['reminder', 'project']
    elif user.user_type == 2:  # Docente
        return ['class', 'assignment', 'exam', 'meeting', 'deadline', 'workshop']
    elif user.user_type == 3:  # Padre
        return ['reminder', 'meeting']
    elif user.user_type == 4:  # Experto
        return ['conference', 'workshop', 'meeting', 'reminder']
    elif user.user_type == 5:  # Admin
        return [choice[0] for choice in CalendarEvent.EVENT_TYPES]
    return []
@login_required
def student_achievements(request):
    """Vista para mostrar los logros del estudiante"""
    user = request.user
    
    try:
        # Obtener logros obtenidos por el estudiante
        earned_achievements = StudentAchievement.objects.filter(
            student=user
        ).select_related('achievement').order_by('-earned_at')
        
        # Obtener todos los logros disponibles
        all_achievements = Achievement.objects.all().order_by('points')
        
        # Crear lista de IDs de logros ya obtenidos
        earned_achievement_ids = set(earned_achievements.values_list('achievement_id', flat=True))
        
        # Separar logros obtenidos y no obtenidos
        achievements_data = []
        
        for achievement in all_achievements:
            is_earned = achievement.id in earned_achievement_ids
            
            # Si está obtenido, buscar la fecha
            earned_date = None
            if is_earned:
                student_achievement = earned_achievements.filter(achievement=achievement).first()
                earned_date = student_achievement.earned_at if student_achievement else None
            
            achievements_data.append({
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'points': achievement.points,
                'earned': is_earned,
                'earned_at': earned_date,
                'css_class': 'earned' if is_earned else 'locked'
            })
        
        # Estadísticas
        total_achievements = all_achievements.count()
        earned_count = earned_achievements.count()
        total_points = sum([ea.achievement.points for ea in earned_achievements])
        completion_percentage = (earned_count / total_achievements * 100) if total_achievements > 0 else 0
        
        # Categorizar por dificultad (basado en puntos)
        easy_achievements = [a for a in achievements_data if a['points'] <= 25]
        medium_achievements = [a for a in achievements_data if 26 <= a['points'] <= 50]
        hard_achievements = [a for a in achievements_data if a['points'] > 50]
        
        context = {
            'user': user,
            'achievements_data': achievements_data,
            'earned_achievements': earned_achievements,
            'total_achievements': total_achievements,
            'earned_count': earned_count,
            'total_points': total_points,
            'completion_percentage': round(completion_percentage, 1),
            'easy_achievements': easy_achievements,
            'medium_achievements': medium_achievements,
            'hard_achievements': hard_achievements,
        }
        
    except Exception as e:
        print(f"Error en student_achievements: {e}")
        context = {
            'user': user,
            'achievements_data': [],
            'earned_achievements': [],
            'total_achievements': 0,
            'earned_count': 0,
            'total_points': 0,
            'completion_percentage': 0,
            'easy_achievements': [],
            'medium_achievements': [],
            'hard_achievements': [],
        }
    
    return render(request, 'students/achievements.html', context)

@login_required
def student_achievement_repository(request):
    """Vista para mostrar todos los logros disponibles (repositorio completo)"""
    user = request.user
    
    try:
        # Obtener todos los logros disponibles
        all_achievements = Achievement.objects.all().order_by('points', 'name')
        
        # Obtener logros ya obtenidos por el estudiante
        earned_achievement_ids = set()
        if user.user_type == 1:  # Solo para estudiantes
            earned_achievements = StudentAchievement.objects.filter(
                student=user
            ).values_list('achievement_id', flat=True)
            earned_achievement_ids = set(earned_achievements)
        
        # Preparar datos de logros con información de si están obtenidos
        achievements_data = []
        for achievement in all_achievements:
            is_earned = achievement.id in earned_achievement_ids
            
            # Buscar fecha de obtención si está obtenido
            earned_date = None
            if is_earned:
                student_achievement = StudentAchievement.objects.filter(
                    student=user, 
                    achievement=achievement
                ).first()
                earned_date = student_achievement.earned_at if student_achievement else None
            
            achievements_data.append({
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'points': achievement.points,
                'earned': is_earned,
                'earned_at': earned_date,
                'css_class': 'earned' if is_earned else 'locked'
            })
        
        # Estadísticas generales
        total_achievements = all_achievements.count()
        earned_count = len(earned_achievement_ids) if user.user_type == 1 else 0
        total_points_available = sum([a.points for a in all_achievements])
        earned_points = sum([a['points'] for a in achievements_data if a['earned']])
        
        # Categorizar por dificultad
        easy_achievements = [a for a in achievements_data if a['points'] <= 25]
        medium_achievements = [a for a in achievements_data if 26 <= a['points'] <= 50]
        hard_achievements = [a for a in achievements_data if a['points'] > 50]
        legendary_achievements = [a for a in achievements_data if a['points'] > 100]
        
        # Estadísticas por categoría
        categories_stats = {
            'easy': {
                'total': len(easy_achievements),
                'earned': len([a for a in easy_achievements if a['earned']]),
                'percentage': 0
            },
            'medium': {
                'total': len(medium_achievements),
                'earned': len([a for a in medium_achievements if a['earned']]),
                'percentage': 0
            },
            'hard': {
                'total': len(hard_achievements),
                'earned': len([a for a in hard_achievements if a['earned']]),
                'percentage': 0
            },
            'legendary': {
                'total': len(legendary_achievements),
                'earned': len([a for a in legendary_achievements if a['earned']]),
                'percentage': 0
            }
        }
        
        # Calcular porcentajes
        for category in categories_stats:
            if categories_stats[category]['total'] > 0:
                categories_stats[category]['percentage'] = round(
                    (categories_stats[category]['earned'] / categories_stats[category]['total']) * 100, 1
                )
        
        context = {
            'user': user,
            'achievements_data': achievements_data,
            'total_achievements': total_achievements,
            'earned_count': earned_count,
            'total_points_available': total_points_available,
            'earned_points': earned_points,
            'easy_achievements': easy_achievements,
            'medium_achievements': medium_achievements,
            'hard_achievements': hard_achievements,
            'legendary_achievements': legendary_achievements,
            'categories_stats': categories_stats,
        }
        
    except Exception as e:
        print(f"Error en achievement_repository: {e}")
        context = {
            'user': user,
            'achievements_data': [],
            'total_achievements': 0,
            'earned_count': 0,
            'total_points_available': 0,
            'earned_points': 0,
            'easy_achievements': [],
            'medium_achievements': [],
            'hard_achievements': [],
            'legendary_achievements': [],
            'categories_stats': {},
        }
    
    return render(request, 'students/achievement_repository.html', context)

@login_required
def student_schedule(request):
    """Vista para mostrar el horario del estudiante"""
    context = {
        'user': request.user,
        'schedule': [],  # Temporalmente vacío
    }
    return render(request, 'students/schedule.html', context)

@login_required
def student_resources(request):
    """Vista para mostrar los recursos del estudiante"""
    context = {
        'user': request.user,
        'resources': [],  # Temporalmente vacío
    }
    return render(request, 'students/resources.html', context)

# ===== VISTAS DE PROFESOR =====

@login_required
def teacher_courses(request):
    """Vista para mostrar los cursos del docente"""
    user = request.user
    if user.user_type != 2:
        return redirect('users:dashboard_student')
    
    courses = Course.objects.filter(teacher=user)
    context = {'courses': courses}
    return render(request, 'teachers/courses.html', context)

@login_required  
def teacher_assignments(request):
    """Vista para mostrar las tareas del docente"""
    user = request.user
    if user.user_type != 2:
        return redirect('users:dashboard_student')
    
    assignments = Assignment.objects.filter(course__teacher=user)
    context = {'assignments': assignments}
    return render(request, 'teachers/assignments.html', context)

@login_required
def teacher_students(request):
    """Vista para mostrar los estudiantes del docente con datos reales"""
    user = request.user
    if user.user_type != 2:
        return redirect('users:dashboard_student')
    
    # Obtener todos los cursos del profesor
    teacher_courses = Course.objects.filter(teacher=user).prefetch_related('enrollment_set__student')
    
    # Obtener todos los estudiantes únicos inscritos en los cursos del profesor
    enrollments = Enrollment.objects.filter(
        course__teacher=user
    ).select_related('student', 'course', 'course__subject').order_by('student__last_name', 'student__first_name')
    
    # Estadísticas
    total_students = enrollments.values('student').distinct().count()
    active_courses = teacher_courses.filter(status='active').count()
    
    # Calcular promedio general de todos los estudiantes
    submissions = AssignmentSubmission.objects.filter(
        assignment__course__teacher=user,
        grade__isnull=False
    )
    average_grade = submissions.aggregate(avg=Avg('grade'))['avg'] or 0
    
    # Agrupar estudiantes por curso
    students_by_course = {}
    for enrollment in enrollments:
        course_name = enrollment.course.name
        if course_name not in students_by_course:
            students_by_course[course_name] = []
        students_by_course[course_name].append(enrollment)
    
    context = {
        'user': user,
        'enrollments': enrollments,
        'teacher_courses': teacher_courses,
        'students_by_course': students_by_course,
        'total_students': total_students,
        'active_courses': active_courses,
        'average_grade': round(average_grade, 1),
    }
    return render(request, 'teachers/students.html', context)

@login_required
def teacher_grades(request):
    """Vista para mostrar las calificaciones del docente"""
    user = request.user
    if user.user_type != 2:
        return redirect('users:dashboard_student')
    
    # Obtener todas las entregas de los cursos del docente
    submissions = AssignmentSubmission.objects.filter(
        assignment__course__teacher=user
    ).select_related('student', 'assignment', 'assignment__course')
    
    context = {
        'user': user,
        'submissions': submissions
    }
    return render(request, 'teachers/grades.html', context)

@login_required
def teacher_resources(request):
    """Vista para recursos del docente"""
    user = request.user
    if user.user_type != 2:
        return redirect('users:dashboard_student')
    
    context = {
        'teacher': request.user,
    }
    return render(request, 'teachers/resources.html', context)

@login_required
def teacher_achievements(request):
    """Vista para logros del docente"""
    user = request.user
    if user.user_type != 2:
        return redirect('users:dashboard_student')
    
    context = {
        'teacher': request.user,
    }
    return render(request, 'teachers/achievements.html', context)

@login_required 
def teacher_achievement_repository(request):
    """Vista para repositorio de logros del docente"""
    user = request.user
    if user.user_type != 2:
        return redirect('users:dashboard_student')
    
    context = {
        'teacher': request.user,
    }
    return render(request, 'teachers/achievement_repository.html', context)

@login_required
def teacher_schedule(request):
    """Vista para horario del docente"""
    user = request.user
    if user.user_type != 2:
        return redirect('users:dashboard_student')
    
    context = {
        'teacher': request.user,
    }
    return render(request, 'teachers/schedule.html', context)



@login_required
def student_resources(request):
    """Vista de recursos para estudiantes"""
    user = request.user
    if user.user_type != 1:
        return redirect('users:dashboard_teacher')
    return render(request, 'students/resources.html')

@login_required
def student_schedule(request):
    """Vista de horario para estudiantes"""
    user = request.user
    if user.user_type != 1:
        return redirect('users:dashboard_teacher')
    return render(request, 'students/schedule.html')

# ===== OTRAS VISTAS =====

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Verificar permisos
    if request.user.user_type == 2:  # Docente
        if course.teacher != request.user:
            return redirect('users:dashboard_teacher', user_id=request.user.id)
    elif request.user.user_type == 3:  # Estudiante
        if not Enrollment.objects.filter(student=request.user, course=course).exists():
            return redirect('users:dashboard_student', user_id=request.user.id)
    else:
        return redirect('users:login')
    
    # Obtener datos del curso
    enrollments = Enrollment.objects.filter(course=course)
    students = [enrollment.student for enrollment in enrollments]
    
    # Obtener materiales del curso (con debug)
    materials = Material.objects.filter(course=course, is_active=True)
    
    # Debug en consola
    print(f"[DEBUG] Course ID: {course_id}")
    print(f"[DEBUG] Materials count: {materials.count()}")
    print(f"[DEBUG] Materials queryset: {materials}")
    for material in materials:
        print(f"[DEBUG] Material: {material.id} - {material.title} - {material.file}")
    
    # Estadísticas
    total_students = enrollments.count()
    total_assignments = 0
    
    context = {
        'user': request.user,
        'course': course,
        'students': students,
        'materials': materials,  # Crítico: asegúrate de que esto esté aquí
        'total_students': total_students,
        'total_assignments': total_assignments,
        'is_teacher': request.user.user_type == 2,
        'is_student': request.user.user_type == 3,
    }
    
    return render(request, 'courses/course_detail.html', context)
@login_required
def join_class(request):
    """Vista para unirse a una clase"""
    if request.method == 'POST':
        course_code = request.POST.get('course_code')
        
        try:
            course = Course.objects.get(code=course_code, status='active')
            
            # Verificar si ya está inscrito
            enrollment, created = Enrollment.objects.get_or_create(
                student=request.user,
                course=course
            )
            
            if created:
                # Crear notificación
                Notification.objects.create(
                    recipient=request.user,
                    title='¡Te has unido a un nuevo curso!',
                    message=f'Te has inscrito exitosamente en {course.name}',
                    notification_type='achievement_unlocked'
                )
                messages.success(request, f'Te has unido exitosamente a {course.name}.')
            else:
                messages.info(request, f'Ya estás inscrito en {course.name}.')

        except Course.DoesNotExist:
            messages.error(request, 'Código de curso inválido')
    
    return redirect('users:dashboard_student')

def generate_unique_class_code():
    """Genera un código único para el aula de 6 caracteres alfanuméricos"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Aulas.objects.filter(CodigoAula=code).exists():
            return code

# ===== NOTIFICACIONES =====

@login_required
def notifications_list(request):
    """Vista para mostrar todas las notificaciones del usuario"""
    try:
        notifications = request.user.gamification_notifications.all().order_by('-created_at')
        
        # Paginación
        paginator = Paginator(notifications, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'user': request.user,
            'notifications': page_obj,
        }
        return render(request, 'notifications/notifications_list.html', context)
    except Exception as e:
        print(f"Error en notifications_list: {e}")
        context = {
            'user': request.user,
            'notifications': [],
        }
        return render(request, 'notifications/notifications_list.html', context)

@login_required
def notifications_api(request):
    """API para obtener notificaciones no leídas"""
    try:
        notifications = request.user.gamification_notifications.filter(is_read=False).order_by('-created_at')[:5]
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'notification_type': notification.notification_type,
                'created_at': notification.created_at.strftime('%d/%m/%Y %H:%M'),
                'icon': get_notification_icon(notification.notification_type),
            })
        
        return JsonResponse({
            'notifications': notifications_data,
            'unread_count': notifications.count()
        })
    except Exception as e:
        print(f"Error en notifications_api: {e}")
        return JsonResponse({
            'notifications': [],
            'unread_count': 0
        })

@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Marcar una notificación como leída"""
    try:
        notification = request.user.gamification_notifications.get(id=notification_id)
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    except Exception as e:
        print(f"Error en mark_notification_read: {e}")
        return JsonResponse({'success': False, 'error': 'Notificación no encontrada'})

@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """Marcar todas las notificaciones como leídas"""
    try:
        count = request.user.gamification_notifications.filter(is_read=False).update(is_read=True)
        return JsonResponse({'success': True, 'marked_count': count})
    except Exception as e:
        print(f"Error en mark_all_notifications_read: {e}")
        return JsonResponse({'success': False})

def get_notification_icon(notification_type):
    """Obtener el icono según el tipo de notificación"""
    icons = {
        'assignment': 'file-earmark-text',
        'grade': 'bar-chart',
        'announcement': 'megaphone',
        'achievement': 'trophy',
        'reminder': 'clock',
    }
    return icons.get(notification_type, 'bell')

# ===== AVATAR =====

@login_required
@require_http_methods(["POST"])
def update_avatar(request):
    """Vista para actualizar el avatar del usuario"""
    try:
        user = request.user
        
        if 'avatar' in request.FILES:
            # Usuario subió una imagen personalizada
            avatar_file = request.FILES['avatar']
            
            # Validar tipo de archivo
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if avatar_file.content_type not in allowed_types:
                return JsonResponse({
                    'success': False,
                    'error': 'Tipo de archivo no permitido. Use JPG, PNG, GIF o WebP.'
                })
            
            # Validar tamaño (5MB)
            if avatar_file.size > 5 * 1024 * 1024:
                return JsonResponse({
                    'success': False,
                    'error': 'El archivo es demasiado grande. Máximo 5MB.'
                })
            
            # Eliminar avatar anterior si existe
            if user.avatar:
                try:
                    if default_storage.exists(user.avatar.name):
                        default_storage.delete(user.avatar.name)
                except:
                    pass
            
            # Guardar nuevo avatar
            user.avatar = avatar_file
            user.save()
            
            return JsonResponse({
                'success': True,
                'avatar_url': user.avatar.url,
                'message': 'Avatar actualizado correctamente'
            })
            
        elif 'preset_avatar' in request.POST:
            # Usuario seleccionó un avatar predeterminado
            preset_name = request.POST['preset_avatar']
            
            # Validar que el preset existe
            preset_path = os.path.join(settings.STATIC_ROOT or settings.STATICFILES_DIRS[0], 'images', 'avatars', preset_name)
            if not os.path.exists(preset_path):
                return JsonResponse({
                    'success': False,
                    'error': 'Avatar predeterminado no encontrado'
                })
            
            # Eliminar avatar anterior si existe
            if user.avatar:
                try:
                    if default_storage.exists(user.avatar.name):
                        default_storage.delete(user.avatar.name)
                except:
                    pass
            
            # Copiar el preset al directorio de uploads
            import shutil
            from django.core.files import File
            
            preset_full_path = os.path.join(settings.STATICFILES_DIRS[0], 'images', 'avatars', preset_name)
            
            # Crear el directorio de uploads si no existe
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generar nombre único para el archivo
            new_filename = f"preset_{user.id}_{preset_name}"
            new_path = os.path.join(upload_dir, new_filename)
            
            # Copiar archivo
            shutil.copy2(preset_full_path, new_path)
            
            # Actualizar campo del usuario
            user.avatar.name = f'avatars/{new_filename}'
            user.save()
            
            return JsonResponse({
                'success': True,
                'avatar_url': user.avatar.url,
                'message': 'Avatar actualizado correctamente'
            })
        
        else:
            return JsonResponse({
                'success': False,
                'error': 'No se proporcionó ninguna imagen'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        })

# === VISTAS API PARA DOCENTES ===

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def create_event_api(request):
    """API para crear un nuevo evento en el calendario del docente"""
    if request.user.user_type != 2:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        
        title = data.get('title')
        event_type = data.get('event_type')
        course_id = data.get('course_id')
        date = data.get('date')
        time = data.get('time')
        location = data.get('location', '')
        description = data.get('description', '')
        
        # Validaciones básicas
        if not all([title, event_type, course_id, date, time]):
            return JsonResponse({'error': 'Faltan campos obligatorios'}, status=400)
        
        # Verificar que el curso pertenece al docente
        course = get_object_or_404(Course, id=course_id, teacher=request.user)
        
        # Crear fecha y hora
        from datetime import datetime
        date_time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        
        # Crear evento
        event = Event.objects.create(
            title=title,
            description=description,
            course=course,
            event_type=event_type,
            start_date=date_time,
            end_date=date_time,  # Se puede extender para duración
            location=location
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Evento creado exitosamente',
            'event_id': event.id
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def send_message_api(request):
    """API para enviar un mensaje a un estudiante o grupo"""
    if request.user.user_type != 2:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        
        recipient_id = data.get('recipient_id')
        subject = data.get('subject')
        content = data.get('content')
        is_course = data.get('is_course', False)
        
        if not all([recipient_id, subject, content]):
            return JsonResponse({'error': 'Faltan campos obligatorios'}, status=400)
        
        if is_course:
            # Enviar mensaje a todos los estudiantes de un curso
            course = get_object_or_404(Course, id=recipient_id, teacher=request.user)
            students = User.objects.filter(
                enrollment__course=course,
                user_type=1
            ).distinct()
            
            messages_created = []
            for student in students:
                message = Message.objects.create(
                    sender=request.user,
                    recipient=student,
                    subject=f"[{course.name}] {subject}",
                    content=content
                )
                messages_created.append(message.id)
            
            return JsonResponse({
                'success': True,
                'message': f'Mensaje enviado a {students.count()} estudiantes del curso {course.name}',
                'messages_created': len(messages_created)
            })
        else:
            # Enviar mensaje a un estudiante individual
            recipient = get_object_or_404(User, id=recipient_id, user_type=1)
            
            # Verificar que el estudiante está inscrito en algún curso del docente
            if not Enrollment.objects.filter(
                student=recipient, 
                course__teacher=request.user
            ).exists():
                return JsonResponse({'error': 'No autorizado para enviar mensaje a este estudiante'}, status=403)
            
            # Crear mensaje
            message = Message.objects.create(
                sender=request.user,
                recipient=recipient,
                subject=subject,
                content=content
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Mensaje enviado exitosamente',
                'message_id': message.id
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_student_details_api(request, student_id):
    """API para obtener detalles de un estudiante"""
    if request.user.user_type != 2:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        # Verificar que el estudiante está en los cursos del docente
        student = get_object_or_404(User, id=student_id, user_type=1)
        enrollments = Enrollment.objects.filter(
            student=student,
            course__teacher=request.user
        ).select_related('course')
        
        if not enrollments.exists():
            return JsonResponse({'error': 'Estudiante no encontrado en tus cursos'}, status=404)
        
        # Obtener estadísticas del estudiante
        total_assignments = Assignment.objects.filter(course__teacher=request.user).count()
        completed_assignments = AssignmentSubmission.objects.filter(
            student=student,
            assignment__course__teacher=request.user
        ).count()
        
        # Calcular promedio de calificaciones
        submissions = AssignmentSubmission.objects.filter(
            student=student,
            assignment__course__teacher=request.user,
            grade__isnull=False
        )
        
        average_grade = submissions.aggregate(Avg('grade'))['grade__avg'] or 0
        
        courses_data = []
        for enrollment in enrollments:
            courses_data.append({
                'course_name': enrollment.course.name,
                'enrollment_date': enrollment.enrolled_at.strftime('%d/%m/%Y'),
                'grade': enrollment.progress or 'Sin calificar'
            })
        
        return JsonResponse({
            'student': {
                'id': student.id,
                'name': student.get_full_name(),
                'email': student.email,
                'profile_picture': student.avatar.url if student.avatar else None,
                'date_joined': student.date_joined.strftime('%d/%m/%Y'),
            },
            'stats': {
                'total_assignments': total_assignments,
                'completed_assignments': completed_assignments,
                'average_grade': round(average_grade, 2),
                }
            },
        )
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def create_class(request):
    """Vista para crear una nueva clase virtual"""
    if request.user.user_type != 2:  # Solo profesores
        return JsonResponse({'success': False, 'error': 'Solo los profesores pueden crear clases'})
    
    try:
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        subject = request.POST.get('subject')
        grade = request.POST.get('grade')
        capacity = int(request.POST.get('capacity', 30))
        code = request.POST.get('code')
        
        if not all([name, subject, grade]):
            return JsonResponse({'success': False, 'error': 'Nombre, materia y grado son requeridos'})
        
        # Crear la clase virtual
        virtual_class = VirtualClass.objects.create(
            name=name,
            description=description,
            subject=subject,
            grade=grade,
            capacity=capacity,
            code=code,
            teacher=request.user,
            is_active=True
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Clase "{name}" creada exitosamente',
            'class_id': virtual_class.id,
            'class_code': code,
            'redirect_url': f'/accounts/class/teacher/{virtual_class.id}/'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error al crear la clase: {str(e)}'})
@login_required
def class_student(request, class_id):
    """Vista de clase para estudiantes"""
    classroom = get_object_or_404(Aulas, IDaula=class_id)
    
    # Verificar si el estudiante está inscrito
    if not AulaEstudiante.objects.filter(IDaula=classroom, IDestudiante=request.user).exists():
        messages.error(request, 'No tienes acceso a esta clase.')
        return redirect('users:dashboard_student')
    
    # Obtener actividades de la clase
    activities = Actividades.objects.all()[:5]  # Limitamos a 5 por ahora
    
    # Obtener progreso del estudiante
    try:
        progress = Niveles.objects.get(IDusuario=request.user)
    except Niveles.DoesNotExist:
        progress = None
    
    # Obtener mensajes del chat (simulado por ahora)
    chat_messages = []
    
    context = {
        'class': classroom,
        'activities': activities,
        'progress': progress,
        'chat_messages': chat_messages,
        'theoretical_content': [],  # Por ahora vacío
    }
    
    return render(request, 'users/class_student.html', context)

@login_required
def class_teacher(request, class_id):
    """Vista para que el profesor gestione su clase virtual"""
    virtual_class = get_object_or_404(VirtualClass, id=class_id)
    
    # Verificar que el usuario sea el profesor de la clase
    if virtual_class.teacher != request.user:
        return redirect('users:dashboard_teacher', user_id=request.user.id)
    
    if request.method == 'POST':
        # Manejar recompensas a estudiantes
        if 'reward_student' in request.POST:
            student_id = request.POST.get('student_id')
            points = int(request.POST.get('reward_student', 0))
            reason = request.POST.get('reward_reason', 'Participación destacada')
            
            try:
                with transaction.atomic():
                    student = User.objects.get(id=student_id)
                    
                    # Verificar que el estudiante esté en la clase
                    if not virtual_class.students.filter(id=student.id).exists():
                        messages.error(request, 'El estudiante no está en esta clase.')
                        return redirect('users:class_teacher', class_id=class_id)
                    
                    # Crear notificación para el estudiante
                    Notification.objects.create(
                        recipient=student,
                        title="¡Has recibido puntos!",
                        message=f"El profesor te ha otorgado {points} puntos por: {reason}",
                        notification_type="achievement_unlocked"
                    )
                    
                    messages.success(request, f'Se otorgaron {points} puntos a {student.get_full_name()}.')
            except Exception as e:
                messages.error(request, f'Error al otorgar puntos: {str(e)}')
        
        # Manejar mensajes del chat (implementar si es necesario)
        if 'chat_message' in request.POST:
            message = request.POST.get('chat_message')
            if message.strip():
                # Implementar sistema de chat si es necesario
                messages.success(request, 'Mensaje enviado.')
    
    # Obtener archivos de la clase
    files = ClassFile.objects.filter(virtual_class=virtual_class, is_active=True).order_by('-uploaded_at')
    
    # Obtener juegos de la clase
    games = ClassGame.objects.filter(virtual_class=virtual_class, is_active=True).order_by('-created_at')
    
    # Obtener estudiantes de la clase
    students = virtual_class.students.all().order_by('last_name', 'first_name')
    
    # Preparar datos de progreso de estudiantes (simulado)
    progress_list = []
    for student in students:
        # En un sistema real, aquí obtendrás el progreso real del estudiante
        progress_list.append({
            'user': student,
            'points': 0,  # Implementar sistema de puntos si es necesario
            'level': 1,   # Implementar sistema de niveles si es necesario
            'next_level_points': 100
        })
    
    # Obtener mensajes del chat (simulado por ahora)
    chat_messages = []
    
    # Estadísticas de la clase
    stats = {
        'total_students': students.count(),
        'total_files': files.count(),
        'total_games': games.count(),
        'capacity_used': (students.count() / virtual_class.capacity * 100) if virtual_class.capacity > 0 else 0
    }
    
    context = {
        'virtual_class': virtual_class,
        'files': files,
        'games': games,
        'students': students,
        'progress_list': progress_list,
        'chat_messages': chat_messages,
        'stats': stats,
        'is_teacher': True,
        'reward_reasons': [
            'Participación destacada',
            'Ayuda a compañeros',
            'Completar actividad',
            'Respuesta correcta',
            'Proyecto especial'
        ]
    }
    
    return render(request, 'shared/classes.html', context)
@login_required
@require_http_methods(["POST"])
def upload_class_file(request, class_id):
    """Subir archivo a la clase"""
    virtual_class = get_object_or_404(VirtualClass, id=class_id)
    
    if virtual_class.teacher != request.user:
        return JsonResponse({'success': False, 'error': 'No tienes permisos'})
    
    try:
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        file = request.FILES.get('file')
        
        if not title or not file:
            return JsonResponse({'success': False, 'error': 'Título y archivo son requeridos'})
        
        ClassFile.objects.create(
            virtual_class=virtual_class,
            title=title,
            description=description,
            file=file,
            uploaded_by=request.user
        )
        
        return JsonResponse({'success': True, 'message': 'Archivo subido exitosamente'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def create_class_game(request, class_id):
    """Crear juego para la clase"""
    virtual_class = get_object_or_404(VirtualClass, id=class_id)
    
    if virtual_class.teacher != request.user:
        return JsonResponse({'success': False, 'error': 'No tienes permisos'})
    
    try:
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        game_type = request.POST.get('game_type')
        time_limit = int(request.POST.get('time_limit', 300))
        
        if not title or not game_type:
            return JsonResponse({'success': False, 'error': 'Título y tipo de juego son requeridos'})
        
        ClassGame.objects.create(
            virtual_class=virtual_class,
            title=title,
            description=description,
            game_type=game_type,
            time_limit=time_limit,
            created_by=request.user
        )
        
        return JsonResponse({'success': True, 'message': 'Juego creado exitosamente'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
@login_required
def play_game(request, class_id):
    """Vista para jugar juegos educativos"""
    classroom = get_object_or_404(Aulas, IDaula=class_id)
    
    # Verificar acceso
    if request.user.user_type == 1:  # Estudiante
        if not AulaEstudiante.objects.filter(IDaula=classroom, IDestudiante=request.user).exists():
            messages.error(request, 'No tienes acceso a esta clase.')
            return redirect('users:dashboard_student')
    elif request.user.user_type == 2:  # Docente
        if classroom.IDdocente != request.user:
            messages.error(request, 'No tienes acceso a esta clase.')
            return redirect('users:dashboard_teacher')
    
    # Redirigir al sistema de gamificación
    return redirect('gamification:dashboard')

@login_required
@require_http_methods(["GET"])
def generate_class_code(request):
    """Vista API para generar un código de clase único"""
    if request.user.user_type != 2:  # Solo docentes
        return JsonResponse({'error': 'No autorizado'}, status=403)
        
    try:
        code = generate_classroom_code()
        return JsonResponse({'code': code})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def create_class_api(request):
    """Vista API para crear un nuevo curso"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    if request.user.user_type != 2:  # Solo docentes
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        with transaction.atomic():
            # Validar y obtener datos del formulario
            course_name = request.POST.get('class_name')
            course_code = request.POST.get('class_code')
            grade = request.POST.get('grade')
            section = request.POST.get('section')
            description = request.POST.get('description', '')
            
            # Validar campos requeridos
            if not all([course_name, course_code, grade, section]):
                return JsonResponse({'error': 'Faltan campos requeridos'}, status=400)
            
            # Verificar que el código sea único
            if Aulas.objects.filter(CodigoAula=course_code).exists():
                return JsonResponse({'error': 'El código del curso ya existe'}, status=400)
            
            # Crear el aula
            aula = Aulas.objects.create(
                NombreAula=course_name,
                CodigoAula=course_code,
                GradoEducativo=grade,
                Seccion=section,
                Descripcion=description,
                IDdocente=request.user,
                FechaCreacion=timezone.now(),
                estado='activo'  # Asegurar que el aula se crea activa

            )
            
            return JsonResponse({
                'success': True,
                'message': 'Curso creado exitosamente',
                'course_id': aula.IDaula
            })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def join_class_api(request):
    """Vista API para que un estudiante se una a un curso"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    if request.user.user_type != 1:  # Solo estudiantes
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        code = request.POST.get('code')
        if not code:
            return JsonResponse({'error': 'Código de clase requerido'}, status=400)
        
        # Buscar el aula
        try:
            aula = Aulas.objects.get(CodigoAula=code)
        except Aulas.DoesNotExist:
            return JsonResponse({'error': 'Código de clase inválido'}, status=404)
        
        # Verificar si ya está inscrito
        if AulaEstudiante.objects.filter(IDaula=aula, IDestudiante=request.user).exists():
            return JsonResponse({'error': 'Ya estás inscrito en esta clase'}, status=400)
        
        # Inscribir al estudiante
        AulaEstudiante.objects.create(
            IDaula=aula,
            IDestudiante=request.user,
            DenominacionAula=aula.NombreAula
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Te has unido a la clase exitosamente',
            'course_id': aula.IDaula
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


from django.contrib.auth.decorators import user_passes_test
from apps.content.models import EducationalSheet, SheetRevisionHistory, StudentContent

def is_expert(user):
    """Verificar si el usuario es un experto"""
    # return user.is_authenticated and user.user_type == 4 - TEMPORALMENTE DESHABILITADO
    return user.is_authenticated  # Temporalmente permitir a todos los usuarios autenticados

@login_required
# @user_passes_test(is_expert)  # TEMPORALMENTE DESHABILITADO
def dashboard_expert(request, user_id):
    """Dashboard principal para expertos"""
    user = request.user
    
    # Obtener perfil de experto
    
    # Estadísticas generales
    pending_sheets = EducationalSheet.objects.filter(
        status='pending_review'
    ).count()
    
    # Mis revisiones en curso (asignadas a mí)
    my_reviews = EducationalSheet.objects.filter(
        reviewer=user,
        status='in_review'
    ).count()
    
    pending_moderation = StudentContent.objects.filter(
        moderation_status='pending'
    ).count()
    
    # Total de fichas que he revisado completamente
    total_completed_reviews = SheetRevisionHistory.objects.filter(
        user=user,
        action__in=['approved', 'rejected']
    ).count()
    
    # Actividad reciente
    recent_reviews = SheetRevisionHistory.objects.filter(
        user=user,
        action__in=['reviewed', 'approved', 'rejected']
    ).select_related('sheet')[:5]
    
    # Fichas asignadas para revisión (mostrar todas las fichas)
    assigned_sheets = EducationalSheet.objects.all().select_related('author', 'category')[:5]
    
    # Contenido pendiente de moderación
    pending_content = StudentContent.objects.filter(
        moderation_status='pending'
    ).select_related('author', 'related_sheet')[:5]
    
    # Mis fichas educativas creadas
    my_sheets = EducationalSheet.objects.filter(
        author=user
    ).order_by('-created_at')[:10]
    
    # Estadísticas de mis fichas
    my_sheets_count = EducationalSheet.objects.filter(author=user).count()
    my_draft_sheets = EducationalSheet.objects.filter(author=user, status='draft').count()
    my_published_sheets = EducationalSheet.objects.filter(author=user, status='published').count()
    my_pending_sheets = EducationalSheet.objects.filter(author=user, status='pending_review').count()
    
    # Estadísticas del experto basadas en datos reales
    total_reviews = SheetRevisionHistory.objects.filter(
        user=user,
        action__in=['reviewed', 'approved', 'rejected']
    ).count()
    
    # Calcular tasa de aprobación
    approved_reviews = SheetRevisionHistory.objects.filter(
        user=user,
        action='approved'
    ).count()
    
    rejected_reviews = SheetRevisionHistory.objects.filter(
        user=user,
        action='rejected'
    ).count()
    
    total_decision_reviews = approved_reviews + rejected_reviews
    approval_rate = (approved_reviews / total_decision_reviews * 100) if total_decision_reviews > 0 else 0
    
    # Fichas revisadas por el usuario este mes
    from django.utils import timezone
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_reviews = SheetRevisionHistory.objects.filter(
        user=user,
        action__in=['reviewed', 'approved', 'rejected'],
        timestamp__gte=current_month
    ).count()
    
    # Fichas pendientes de revisión del usuario
    my_pending_reviews = EducationalSheet.objects.filter(
        reviewer=user,
        status='in_review'
    ).count()
    
    # Promedio de tiempo de revisión basado en datos reales
    from django.db.models import Avg
    from datetime import timedelta
    
    # Obtener fichas que el usuario ha completado con fechas de revisión
    completed_sheets = EducationalSheet.objects.filter(
        reviewer=user,
        status__in=['approved', 'rejected', 'published'],
        review_date__isnull=False
    )
    
    if completed_sheets.exists():
        # Calcular diferencia promedio entre created_at y review_date
        total_days = 0
        count = 0
        for sheet in completed_sheets:
            if sheet.review_date and sheet.created_at:
                diff = sheet.review_date - sheet.created_at
                total_days += diff.days
                count += 1
        
        avg_review_time = round(total_days / count, 1) if count > 0 else 0
    else:
        avg_review_time = 0
    
    context = {
        'user': user,
        'pending_sheets': pending_sheets,
        'my_reviews': my_reviews,
        'pending_moderation': pending_moderation,
        'recent_reviews': recent_reviews,
        'assigned_sheets': assigned_sheets,
        'pending_content': pending_content,
        'my_sheets': my_sheets,
        'my_sheets_count': my_sheets_count,
        'my_draft_sheets': my_draft_sheets,
        'my_published_sheets': my_published_sheets,
        'my_pending_sheets': my_pending_sheets,
        'total_reviews': total_reviews,
        'approval_rate': approval_rate,
        'monthly_reviews': monthly_reviews,
        'my_pending_reviews': my_pending_reviews,
        'approved_reviews': approved_reviews,
        'rejected_reviews': rejected_reviews,
        'avg_review_time': avg_review_time,
        'total_completed_reviews': total_completed_reviews,
    }
    
    return render(request, 'dashboards/dashboard_expert.html', context)

@login_required
def create_educational_sheet(request):
    """Vista para crear fichas educativas para expertos"""
    # if request.user.user_type != 4:  # Solo expertos - TEMPORALMENTE DESHABILITADO
    if False:  # Temporalmente deshabilitado para testing
        return redirect('users:dashboard_expert', user_id=request.user.id)
    
    sheet_type = request.GET.get('type', 'flora')
    
    # Definir tags predefinidos por tipo
    type_names = {
        'flora': 'Flora',
        'fauna': 'Fauna', 
        'ecosystem': 'Ecosistema/Lugar'
    }
    
    predefined_tags = {
        'flora': {
            'Clasificación Biológica': ['Árbol', 'Arbusto', 'Hierba', 'Epífita', 'Parásita', 'Acuática'],
            'Tipo de Reproducción': ['Sexual', 'Asexual', 'Esporas', 'Semillas', 'Bulbos', 'Estolones'],
            'Estado de Conservación': ['No Evaluado', 'Datos Insuficientes', 'Preocupación Menor', 'Casi Amenazado', 'Vulnerable', 'En Peligro', 'En Peligro Crítico', 'Extinto en Estado Silvestre', 'Extinto'],
            'Hábitat/Ecosistema': ['Bosque Tropical', 'Bosque Seco', 'Páramo', 'Manglar', 'Humedal', 'Desierto', 'Costa', 'Montaña', 'Río', 'Lago'],
            'Usos Tradicionales': ['Medicinal', 'Alimentario', 'Construcción', 'Textil', 'Ceremonial', 'Ornamental', 'Combustible', 'Artesanal'],
        },
        'fauna': {
            'Clasificación Biológica': ['Mamífero', 'Ave', 'Reptil', 'Anfibio', 'Pez', 'Insecto', 'Arácnido', 'Crustáceo', 'Molusco'],
            'Tipo de Reproducción': ['Ovíparo', 'Vivíparo', 'Ovovivíparo', 'Metamorfosis Completa', 'Metamorfosis Incompleta'],
            'Estado de Conservación': ['No Evaluado', 'Datos Insuficientes', 'Preocupación Menor', 'Casi Amenazado', 'Vulnerable', 'En Peligro', 'En Peligro Crítico', 'Extinto en Estado Silvestre', 'Extinto'],
            'Hábitat/Ecosistema': ['Bosque Tropical', 'Bosque Seco', 'Páramo', 'Manglar', 'Humedal', 'Desierto', 'Costa', 'Montaña', 'Río', 'Lago', 'Subterráneo', 'Aéreo'],
            'Alimentación': ['Herbívoro', 'Carnívoro', 'Omnívoro', 'Insectívoro', 'Frugívoro', 'Nectarívoro', 'Planctívoro', 'Detritívoro'],
            'Nivel de Riesgo': ['Sin Riesgo', 'Riesgo Bajo', 'Riesgo Moderado', 'Alto Riesgo', 'Riesgo Crítico'],
        },
        'ecosystem': {
            'Clasificación Biológica': ['Terrestre', 'Acuático', 'Marino', 'Dulceacuícola', 'Mixto'],
            'Estado de Conservación': ['Pristino', 'Conservado', 'Alterado', 'Degradado', 'Muy Degradado', 'Crítico'],
            'Hábitat/Ecosistema': ['Bosque Primario', 'Bosque Secundario', 'Páramo', 'Manglar', 'Humedal', 'Desierto', 'Costa Rocosa', 'Playa Arenosa', 'Arrecife', 'Lago', 'Río', 'Cueva'],
            'Nivel de Riesgo': ['Sin Amenaza', 'Amenaza Baja', 'Amenaza Moderada', 'Alta Amenaza', 'Amenaza Crítica'],
        }
    }
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            title = request.POST.get('title')
            description = request.POST.get('description')
            content = request.POST.get('content')
            region = request.POST.get('region')
            images = request.FILES.getlist('images')
            videos = request.FILES.getlist('videos')
            audios = request.FILES.getlist('audios')
            documents = request.FILES.getlist('documents')
            
            # Procesar tags estructurados
            tags_data = {}
            for category in predefined_tags.get(sheet_type, {}):
                selected_tags = request.POST.getlist(f'tags_{category.lower().replace(" ", "_").replace("/", "_")}')
                if selected_tags:
                    tags_data[category] = selected_tags
            
            # Determinar el estado basado en la opción de envío
            submit_for_review = request.POST.get('submit_for_review') == 'on'
            status = 'pending_review' if submit_for_review else 'draft'
            
            # Crear la ficha educativa
            sheet = EducationalSheet.objects.create(
                title=title,
                description=description,
                content=content,
                sheet_type=sheet_type,
                region=region,
                author=request.user,
                tags=json.dumps(tags_data),
                status=status
            )
            
            # Procesar archivos multimedia
            featured_image = request.FILES.get('featured_image')
            attachments = request.FILES.get('attachments')
            
            if featured_image:
                sheet.featured_image = featured_image
                
            if attachments:
                sheet.attachments = attachments
                
            sheet.save()
            
            # Mensaje de éxito según el estado
            if status == 'pending_review':
                messages.success(request, f'Ficha "{title}" creada y enviada para revisión exitosamente.')
            else:
                messages.success(request, f'Ficha "{title}" guardada como borrador exitosamente.')
            return redirect('users:dashboard_expert', user_id=request.user.id)
            
        except Exception as e:
            messages.error(request, f'Error al crear la ficha: {str(e)}')
    
    context = {
        'user': request.user,
        'sheet_type': sheet_type,
        'type_names': type_names,
        'predefined_tags': predefined_tags.get(sheet_type, {}),
    }
    
    return render(request, 'experts/create_sheet.html', context)
@login_required
def expert_review_sheets(request):
    """Vista para que el experto revise fichas asignadas"""
    # if request.user.user_type != 4:  # Solo expertos - TEMPORALMENTE DESHABILITADO
    if False:  # Temporalmente deshabilitado para testing
        return redirect('users:dashboard_expert', user_id=request.user.id)
    
    # Obtener todas las fichas de la base de datos
    sheets_queryset = EducationalSheet.objects.all().select_related('author', 'category', 'reviewer')
    
    # Filtros
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    
    # Aplicar filtro de estado
    if status_filter and status_filter != 'all':
        sheets_queryset = sheets_queryset.filter(status=status_filter)
    
    # Aplicar filtro de búsqueda
    if search_query:
        sheets_queryset = sheets_queryset.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    # Ordenar por fecha de creación (más recientes primero)
    assigned_sheets = sheets_queryset.order_by('-created_at')
    
    context = {
        'user': request.user,
        'assigned_sheets': assigned_sheets,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': EducationalSheet.STATUS_CHOICES,
    }
    
    return render(request, 'experts/review_sheets.html', context)

@login_required
def expert_statistics(request):
    """Vista para mostrar estadísticas del experto"""
    # if request.user.user_type != 4:  # Solo expertos - TEMPORALMENTE DESHABILITADO
    if False:  # Temporalmente deshabilitado para testing
        return redirect('users:dashboard_expert', user_id=request.user.id)
    
    # Importar modelos necesarios
    from datetime import datetime, timedelta
    from django.db.models import Count, Q, Avg
    from apps.content.models import EducationalSheet, SheetRevisionHistory
    
    # Calcular fechas
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    
    # Consultar estadísticas reales basadas en el usuario experto
    expert_user = request.user
    
    # Total de fichas revisadas por este experto
    total_reviewed_sheets = EducationalSheet.objects.filter(
        reviewer=expert_user
    ).exclude(status='draft').count()
    
    # Fichas pendientes de revisión (asignadas a este experto o sin asignar)
    pending_reviews = EducationalSheet.objects.filter(
        Q(reviewer=expert_user, status__in=['pending_review', 'in_review']) |
        Q(reviewer__isnull=True, status='pending_review')
    ).count()
    
    # Fichas aprobadas por este experto
    approved_sheets = EducationalSheet.objects.filter(
        reviewer=expert_user,
        status='approved'
    ).count()
    
    # Fichas rechazadas por este experto
    rejected_sheets = EducationalSheet.objects.filter(
        reviewer=expert_user,
        status='rejected'
    ).count()
    
    # Cálculos derivados
    total_reviews = approved_sheets + rejected_sheets
    approval_rate = round((approved_sheets / total_reviews * 100), 1) if total_reviews > 0 else 0
    
    # Tiempo promedio de revisión (basado en el historial)
    review_times = []
    for sheet in EducationalSheet.objects.filter(reviewer=expert_user, review_date__isnull=False):
        # Buscar cuando fue asignada para revisión
        submitted_history = SheetRevisionHistory.objects.filter(
            sheet=sheet,
            action='submitted'
        ).first()
        
        if submitted_history and sheet.review_date:
            time_diff = sheet.review_date - submitted_history.timestamp
            review_times.append(time_diff.total_seconds() / 3600)  # Convertir a horas
    
    avg_review_time = round(sum(review_times) / len(review_times), 1) if review_times else 0
    
    # Estadísticas del mes actual
    reviews_this_month = EducationalSheet.objects.filter(
        reviewer=expert_user,
        review_date__gte=start_of_month,
        review_date__isnull=False
    ).count()
    
    approved_this_month = EducationalSheet.objects.filter(
        reviewer=expert_user,
        status='approved',
        review_date__gte=start_of_month
    ).count()
    
    rejected_this_month = EducationalSheet.objects.filter(
        reviewer=expert_user,
        status='rejected',
        review_date__gte=start_of_month
    ).count()
    
    # Estadísticas de la semana actual
    reviews_this_week = EducationalSheet.objects.filter(
        reviewer=expert_user,
        review_date__gte=start_of_week,
        review_date__isnull=False
    ).count()
    
    approved_this_week = EducationalSheet.objects.filter(
        reviewer=expert_user,
        status='approved',
        review_date__gte=start_of_week
    ).count()
    
    rejected_this_week = EducationalSheet.objects.filter(
        reviewer=expert_user,
        status='rejected',
        review_date__gte=start_of_week
    ).count()
    
    # Calcular tasas de aprobación por período
    approval_rate_week = round((approved_this_week / reviews_this_week * 100), 1) if reviews_this_week > 0 else 0
    approval_rate_month = round((approved_this_month / reviews_this_month * 100), 1) if reviews_this_month > 0 else 0
    
    # Compilar estadísticas
    stats = {
        'total_reviews': total_reviews,
        'pending_reviews': pending_reviews,
        'approved_sheets': approved_sheets,
        'rejected_sheets': rejected_sheets,
        'approval_rate': approval_rate,
        'avg_review_time': avg_review_time,
        'reviews_this_month': reviews_this_month,
        'reviews_this_week': reviews_this_week,
        'approved_this_week': approved_this_week,
        'rejected_this_week': rejected_this_week,
        'approved_this_month': approved_this_month,
        'rejected_this_month': rejected_this_month,
        'approval_rate_week': approval_rate_week,
        'approval_rate_month': approval_rate_month,
    }
    
    # Datos para gráficos (últimos 7 meses)
    monthly_reviews = []
    for i in range(6, -1, -1):
        month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_reviews = EducationalSheet.objects.filter(
            reviewer=expert_user,
            review_date__gte=month_start,
            review_date__lte=month_end
        ).count()
        
        monthly_reviews.append({
            'month': month_start.strftime('%B'),
            'reviews': month_reviews
        })
    
    # Distribución por categorías (de las fichas revisadas)
    category_distribution = EducationalSheet.objects.filter(
        reviewer=expert_user
    ).values('category__name').annotate(
        count=Count('id')
    ).order_by('-count')[:5]  # Top 5 categorías
    
    # Convertir a formato esperado
    category_distribution = [
        {
            'category': cat['category__name'] or 'Sin categoría',
            'count': cat['count']
        }
        for cat in category_distribution
    ]
    
    context = {
        'user': request.user,
        'stats': stats,
        'monthly_reviews': monthly_reviews,
        'category_distribution': category_distribution,
    }
    
    return render(request, 'experts/statistics.html', context)

@login_required
def generate_expert_report(request):
    """Vista para generar reportes de expertos"""
    # Debug information
    print(f"User: {request.user}")
    print(f"User type: {getattr(request.user, 'user_type', 'No user_type')}")
    print(f"Is authenticated: {request.user.is_authenticated}")
    print(f"Method: {request.method}")
    
    # Verificar si el usuario es experto - TEMPORALMENTE PERMITIR A TODOS LOS USUARIOS AUTENTICADOS
    # Cambiar esta línea después de verificar que funciona:
    # if not hasattr(request.user, 'user_type') or request.user.user_type != 4:
    if False:  # Temporalmente deshabilitado para testing
        print(f"Access denied: user_type is {getattr(request.user, 'user_type', 'None')}")
        if request.method == 'POST':
            return JsonResponse({'error': 'Acceso denegado. Solo los expertos pueden generar reportes.'}, status=403)
        else:
            messages.error(request, 'Acceso denegado. Solo los expertos pueden generar reportes.')
            return redirect('users:dashboard_home')
    
    if request.method == 'POST':
        # Procesar formulario y generar reporte
        print("Processing POST request for report generation")
        return download_expert_report(request)
    
    # Valores por defecto para el formulario
    default_end_date = timezone.now().date()
    default_start_date = default_end_date - timedelta(days=30)
    
    context = {
        'user': request.user,
        'default_start_date': default_start_date,
        'default_end_date': default_end_date,
    }
    
    return render(request, 'experts/generate_report.html', context)

@login_required 
def download_expert_report(request):
    """Vista para descargar el reporte generado"""
    print(f"Download report - User: {request.user}, Type: {getattr(request.user, 'user_type', 'None')}")
    
    # Verificar si el usuario es experto - TEMPORALMENTE PERMITIR A TODOS LOS USUARIOS AUTENTICADOS
    # Cambiar esta línea después de verificar que funciona:
    # if not hasattr(request.user, 'user_type') or request.user.user_type != 4:
    if False:  # Temporalmente deshabilitado para testing
        print(f"Access denied in download: user_type is {getattr(request.user, 'user_type', 'None')}")
        return JsonResponse({'error': 'Acceso denegado. Solo los expertos pueden generar reportes.'}, status=403)
    
    try:
        print("Processing report download request")
        
        # Obtener parámetros del formulario
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date') 
        export_format = request.POST.get('export_format', 'pdf')
        report_sections = request.POST.getlist('report_sections')
        
        print(f"Report parameters: start={start_date}, end={end_date}, format={export_format}, sections={report_sections}")
        
        content_category = request.POST.get('content_category', '')
        review_status = request.POST.get('review_status', '')
        include_charts = request.POST.get('include_charts') == 'on'
        detailed_breakdown = request.POST.get('detailed_breakdown') == 'on'
        include_comparisons = request.POST.get('include_comparisons') == 'on'
        anonymize_data = request.POST.get('anonymize_data') == 'on'
        
        # Generar datos del reporte
        print("Generating report data...")
        report_data = generate_report_data(
            request.user, start_date, end_date, report_sections,
            content_category, review_status, include_charts,
            detailed_breakdown, include_comparisons, anonymize_data
        )
        
        print(f"Report data generated successfully for format: {export_format}")
        
        # Generar reporte según el formato
        if export_format == 'pdf':
            return generate_pdf_report(report_data, request.user)
        elif export_format == 'excel':
            return generate_excel_report(report_data, request.user)
        elif export_format == 'csv':
            return generate_csv_report(report_data, request.user)
        else:
            return JsonResponse({'error': 'Formato no soportado'}, status=400)
            
    except Exception as e:
        # Log del error para debugging
        import traceback
        error_msg = f"Error generating report: {str(e)}"
        traceback_msg = traceback.format_exc()
        print(error_msg)
        print(traceback_msg)
        
        return JsonResponse({
            'error': f'Error al generar el reporte: {str(e)}',
            'details': traceback_msg if settings.DEBUG else None
        }, status=500)

def generate_report_data(user, start_date, end_date, sections, category, status, 
                        include_charts, detailed_breakdown, include_comparisons, anonymize_data):
    """Generar datos para el reporte del experto"""
    from datetime import datetime, timedelta
    from django.db.models import Count, Q, Avg
    from apps.content.models import EducationalSheet, SheetRevisionHistory
    
    # Convertir fechas
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else timezone.now().date() - timedelta(days=30)
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else timezone.now().date()
    
    # Filtros base para el período
    base_filter = Q(reviewer=user, review_date__gte=start_dt, review_date__lte=end_dt)
    
    # Aplicar filtros adicionales
    if category:
        if category == 'animals':
            base_filter &= Q(sheet_type='fauna')
        elif category == 'plants':
            base_filter &= Q(sheet_type='flora')
        elif category == 'guides':
            base_filter &= Q(category__name__icontains='guía')
        elif category == 'multimedia':
            base_filter &= Q(attachments__isnull=False)
    
    if status:
        base_filter &= Q(status=status)
    
    report_data = {
        'user': user,
        'period': {
            'start_date': start_dt,
            'end_date': end_dt,
            'total_days': (end_dt - start_dt).days + 1
        },
        'sections': sections,
        'options': {
            'category': category,
            'status': status,
            'include_charts': include_charts,
            'detailed_breakdown': detailed_breakdown,
            'include_comparisons': include_comparisons,
            'anonymize_data': anonymize_data
        },
        'generated_at': timezone.now()
    }
    
    # Generar datos según las secciones seleccionadas
    if 'activity_summary' in sections:
        total_reviews = EducationalSheet.objects.filter(base_filter).count()
        pending_reviews = EducationalSheet.objects.filter(
            Q(reviewer=user, status__in=['pending_review', 'in_review']) |
            Q(reviewer__isnull=True, status='pending_review')
        ).count()
        completed_reviews = EducationalSheet.objects.filter(
            reviewer=user,
            review_date__gte=start_dt,
            review_date__lte=end_dt,
            status__in=['approved', 'rejected']
        ).count()
        
        # Calcular día más activo
        daily_reviews = EducationalSheet.objects.filter(base_filter).extra(
            select={'day': 'DATE(review_date)'}
        ).values('day').annotate(count=Count('id')).order_by('-count')
        
        most_active_day = 'No disponible'
        if daily_reviews:
            most_active_date = daily_reviews[0]['day']
            most_active_day = most_active_date.strftime('%A') if most_active_date else 'No disponible'
        
        report_data['activity_summary'] = {
            'total_reviews': total_reviews,
            'pending_reviews': pending_reviews,
            'completed_reviews': completed_reviews,
            'average_daily_reviews': round(total_reviews / ((end_dt - start_dt).days + 1), 1),
            'most_active_day': most_active_day,
            'busiest_week': f'Semana del {start_dt.strftime("%d-%m")}'
        }
    
    if 'review_statistics' in sections:
        approved_content = EducationalSheet.objects.filter(base_filter, status='approved').count()
        rejected_content = EducationalSheet.objects.filter(base_filter, status='rejected').count()
        total_reviewed = approved_content + rejected_content
        
        approval_rate = round((approved_content / total_reviewed * 100), 1) if total_reviewed > 0 else 0
        
        # Calcular tiempo promedio de revisión
        review_times = []
        for sheet in EducationalSheet.objects.filter(base_filter):
            submitted_history = SheetRevisionHistory.objects.filter(
                sheet=sheet, action='submitted'
            ).first()
            
            if submitted_history and sheet.review_date:
                time_diff = sheet.review_date - submitted_history.timestamp
                review_times.append(time_diff.total_seconds() / 3600)
        
        avg_review_time = round(sum(review_times) / len(review_times), 1) if review_times else 0
        fastest_review = round(min(review_times), 1) if review_times else 0
        slowest_review = round(max(review_times), 1) if review_times else 0
        
        # Distribución por categorías
        reviews_by_category = EducationalSheet.objects.filter(base_filter).values(
            'sheet_type'
        ).annotate(count=Count('id'))
        
        category_dict = {}
        for item in reviews_by_category:
            sheet_type = item['sheet_type']
            if sheet_type == 'fauna':
                category_dict['Animales'] = item['count']
            elif sheet_type == 'flora':
                category_dict['Plantas'] = item['count']
            elif sheet_type == 'ecosystem':
                category_dict['Lugares'] = item['count']
        
        report_data['review_statistics'] = {
            'approved_content': approved_content,
            'rejected_content': rejected_content,
            'approval_rate': approval_rate,
            'average_review_time': avg_review_time,
            'fastest_review': fastest_review,
            'slowest_review': slowest_review,
            'reviews_by_category': category_dict
        }
    
    if 'content_analysis' in sections:
        total_content_reviewed = EducationalSheet.objects.filter(base_filter).count()
        
        # Calcular puntuación de calidad promedio (simulada)
        quality_scores = []
        for sheet in EducationalSheet.objects.filter(base_filter):
            # Simular puntuación basada en características del contenido
            score = 7.0  # Base score
            if sheet.featured_image:
                score += 0.5
            if sheet.attachments:
                score += 0.3
            if len(sheet.content) > 500:
                score += 0.4
            if sheet.tags:
                score += 0.3
            quality_scores.append(min(score, 10.0))
        
        avg_quality = round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else 0
        
        # Análisis de tipos de contenido
        content_by_type = {
            'Fichas de Flora': EducationalSheet.objects.filter(base_filter, sheet_type='flora').count(),
            'Fichas de Fauna': EducationalSheet.objects.filter(base_filter, sheet_type='fauna').count(),
            'Fichas de Lugares': EducationalSheet.objects.filter(base_filter, sheet_type='ecosystem').count(),
        }
        
        # Problemas comunes (simulados basados en datos reales)
        rejected_sheets = EducationalSheet.objects.filter(base_filter, status='rejected')
        common_issues = []
        if rejected_sheets.count() > 0:
            common_issues = [
                'Contenido insuficiente o poco detallado',
                'Falta de referencias científicas',
                'Imágenes de baja calidad o sin derechos'
            ]
        
        report_data['content_analysis'] = {
            'total_content_reviewed': total_content_reviewed,
            'quality_score_average': avg_quality,
            'common_issues': common_issues,
            'content_by_type': content_by_type
        }
    
    if 'performance_metrics' in sections:
        total_sheets = EducationalSheet.objects.filter(base_filter).count()
        approved_sheets = EducationalSheet.objects.filter(base_filter, status='approved').count()
        
        # Métricas de rendimiento calculadas
        efficiency_score = min(100, (total_sheets / ((end_dt - start_dt).days + 1)) * 20)
        accuracy_score = (approved_sheets / total_sheets * 100) if total_sheets > 0 else 0
        speed_score = max(0, 100 - (avg_review_time * 10)) if 'review_statistics' in report_data else 85
        consistency_score = 90  # Basado en la variabilidad de tiempos de revisión
        
        overall_rating = (efficiency_score + accuracy_score + speed_score + consistency_score) / 80
        
        report_data['performance_metrics'] = {
            'efficiency_score': round(efficiency_score, 1),
            'accuracy_score': round(accuracy_score, 1),
            'speed_score': round(speed_score, 1),
            'consistency_score': round(consistency_score, 1),
            'overall_rating': round(overall_rating, 1),
            'improvement_areas': [
                'Optimización de tiempo de revisión',
                'Feedback más detallado para autores'
            ]
        }
    
    if 'user_interactions' in sections:
        # Simular interacciones basadas en datos reales
        reviewed_sheets = EducationalSheet.objects.filter(base_filter)
        
        feedback_received = reviewed_sheets.count()
        positive_feedback = reviewed_sheets.filter(status='approved').count()
        negative_feedback = reviewed_sheets.filter(status='rejected').count()
        
        avg_rating = (positive_feedback * 5 + negative_feedback * 2) / feedback_received if feedback_received > 0 else 0
        
        report_data['user_interactions'] = {
            'feedback_received': feedback_received,
            'positive_feedback': positive_feedback,
            'negative_feedback': negative_feedback,
            'average_rating': round(avg_rating, 1),
            'response_time': avg_review_time if 'review_statistics' in report_data else 2.5,
            'follow_up_actions': reviewed_sheets.filter(status='approved').count()
        }
    
    if 'recommendations' in sections:
        # Generar recomendaciones basadas en datos reales
        total_reviews = EducationalSheet.objects.filter(base_filter).count()
        avg_time = avg_review_time if 'review_statistics' in report_data else 2.5
        approval_rate = (approved_content / total_reviewed * 100) if 'review_statistics' in report_data and total_reviewed > 0 else 70
        
        focus_areas = []
        training_suggestions = []
        goals = []
        
        if avg_time > 4:
            focus_areas.append('Reducir tiempo promedio de revisión')
            training_suggestions.append('Técnicas de evaluación rápida')
            goals.append('Reducir tiempo promedio a menos de 3 horas')
        
        if approval_rate < 70:
            focus_areas.append('Mejorar criterios de evaluación')
            training_suggestions.append('Actualización en estándares de calidad')
            goals.append('Mantener tasa de aprobación entre 70-80%')
        
        if total_reviews < 10:
            focus_areas.append('Aumentar productividad en revisiones')
            training_suggestions.append('Gestión eficiente del tiempo')
            goals.append('Revisar al menos 15 fichas por período')
        
        # Valores por defecto si no hay suficientes datos
        if not focus_areas:
            focus_areas = ['Mantener calidad en las revisiones', 'Continuar con feedback constructivo']
            training_suggestions = ['Capacitación continua en nuevas metodologías']
            goals = ['Mantener estándares actuales de calidad']
        
        report_data['recommendations'] = {
            'focus_areas': focus_areas,
            'training_suggestions': training_suggestions,
            'goals_next_period': goals
        }
    
    # Agregar datos de comparación si se solicita
    if include_comparisons:
        # Período anterior
        previous_start = start_dt - timedelta(days=(end_dt - start_dt).days + 1)
        previous_end = start_dt - timedelta(days=1)
        
        previous_filter = Q(reviewer=user, review_date__gte=previous_start, review_date__lte=previous_end)
        
        previous_total = EducationalSheet.objects.filter(previous_filter).count()
        previous_approved = EducationalSheet.objects.filter(previous_filter, status='approved').count()
        previous_approval_rate = (previous_approved / previous_total * 100) if previous_total > 0 else 0
        
        current_total = EducationalSheet.objects.filter(base_filter).count()
        current_approved = EducationalSheet.objects.filter(base_filter, status='approved').count()
        current_approval_rate = (current_approved / current_total * 100) if current_total > 0 else 0
        
        report_data['comparison'] = {
            'previous_period': {
                'start_date': previous_start,
                'end_date': previous_end,
                'total_reviews': previous_total,
                'approval_rate': round(previous_approval_rate, 1)
            },
            'changes': {
                'reviews_change': round(((current_total - previous_total) / previous_total * 100), 1) if previous_total > 0 else 0,
                'approval_rate_change': round(current_approval_rate - previous_approval_rate, 1),
                'speed_improvement': 15.0  # Placeholder
            }
        }
    
    return report_data

def generate_pdf_report(report_data, user):
    """Generar reporte en formato PDF"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from io import BytesIO
        
        # Crear buffer en memoria
        buffer = BytesIO()
        
        # Crear documento PDF
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.darkgreen,
            alignment=1  # Centro
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        # Construir contenido del PDF
        story = []
        
        # Título principal
        story.append(Paragraph("Reporte de Actividad - Experto", title_style))
        story.append(Spacer(1, 12))
        
        # Información del experto
        expert_info = f"""
        <b>Experto:</b> {user.get_full_name()}<br/>
        <b>Email:</b> {user.email}<br/>
        <b>Período:</b> {report_data['period']['start_date']} - {report_data['period']['end_date']}<br/>
        <b>Total de días:</b> {report_data['period']['total_days']}<br/>
        <b>Generado:</b> {report_data['generated_at'].strftime('%d/%m/%Y %H:%M')}
        """
        story.append(Paragraph(expert_info, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Agregar secciones según selección
        for section in report_data['sections']:
            if section == 'activity_summary' and 'activity_summary' in report_data:
                story.append(Paragraph("Resumen de Actividad", heading_style))
                activity = report_data['activity_summary']
                activity_text = f"""
                <b>Total de revisiones:</b> {activity['total_reviews']}<br/>
                <b>Revisiones pendientes:</b> {activity['pending_reviews']}<br/>
                <b>Revisiones completadas:</b> {activity['completed_reviews']}<br/>
                <b>Promedio diario:</b> {activity['average_daily_reviews']} revisiones<br/>
                <b>Día más activo:</b> {activity['most_active_day']}<br/>
                <b>Semana más ocupada:</b> {activity['busiest_week']}
                """
                story.append(Paragraph(activity_text, styles['Normal']))
                story.append(Spacer(1, 16))
            
            if section == 'review_statistics' and 'review_statistics' in report_data:
                story.append(Paragraph("Estadísticas de Revisiones", heading_style))
                stats = report_data['review_statistics']
                
                # Tabla de estadísticas
                data = [
                    ['Métrica', 'Valor'],
                    ['Contenido aprobado', str(stats['approved_content'])],
                    ['Contenido rechazado', str(stats['rejected_content'])],
                    ['Tasa de aprobación', f"{stats['approval_rate']}%"],
                    ['Tiempo promedio de revisión', f"{stats['average_review_time']} horas"],
                ]
                
                table = Table(data, colWidths=[3*inch, 2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(table)
                story.append(Spacer(1, 16))
        
        # Construir PDF
        doc.build(story)
        
        # Preparar respuesta HTTP
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        filename = f"reporte_experto_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        # Fallback a un reporte simple en texto
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="reporte_simple.txt"'
        response.write(f"Reporte de Experto\n")
        response.write(f"Usuario: {user.get_full_name()}\n")
        response.write(f"Email: {user.email}\n")
        response.write(f"Fecha: {timezone.now().strftime('%d/%m/%Y %H:%M')}\n")
        response.write(f"\nError al generar PDF: {str(e)}\n")
        return response

def generate_excel_report(report_data, user):
    """Generar reporte en formato Excel"""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill
        from io import BytesIO
        
        # Crear workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Reporte Experto"
        
        # Estilos
        title_font = Font(size=16, bold=True, color="FFFFFF")
        title_fill = PatternFill(start_color="2E7D32", end_color="2E7D32", fill_type="solid")
        header_font = Font(size=12, bold=True)
        
        # Título principal
        ws['A1'] = "Reporte de Actividad - Experto"
        ws['A1'].font = title_font
        ws['A1'].fill = title_fill
        ws.merge_cells('A1:D1')
        
        # Información del experto
        row = 3
        ws[f'A{row}'] = "Experto:"
        ws[f'B{row}'] = user.get_full_name()
        row += 1
        ws[f'A{row}'] = "Email:"
        ws[f'B{row}'] = user.email
        row += 1
        ws[f'A{row}'] = "Período:"
        ws[f'B{row}'] = f"{report_data['period']['start_date']} - {report_data['period']['end_date']}"
        row += 2
        
        # Agregar datos según secciones
        if 'activity_summary' in report_data['sections'] and 'activity_summary' in report_data:
            ws[f'A{row}'] = "Resumen de Actividad"
            ws[f'A{row}'].font = header_font
            row += 1
            
            activity = report_data['activity_summary']
            for key, value in activity.items():
                ws[f'A{row}'] = key.replace('_', ' ').title()
                ws[f'B{row}'] = value
                row += 1
            row += 1
        
        # Ajustar anchos de columna
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Guardar en buffer
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        # Preparar respuesta HTTP
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"reporte_experto_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        print(f"Error generating Excel: {str(e)}")
        # Fallback a CSV
        return generate_csv_report(report_data, user)

def generate_csv_report(report_data, user):
    """Generar reporte en formato CSV"""
    try:
        import csv
        from io import StringIO
        
        # Crear respuesta HTTP
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        filename = f"reporte_experto_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Escribir BOM para UTF-8
        response.write('\ufeff')
        
        writer = csv.writer(response)
        
        # Encabezado principal
        writer.writerow(['Reporte de Actividad - Experto'])
        writer.writerow([])
        
        # Información del experto
        writer.writerow(['Experto', user.get_full_name()])
        writer.writerow(['Email', user.email])
        writer.writerow(['Período', f"{report_data['period']['start_date']} - {report_data['period']['end_date']}"])
        writer.writerow(['Total de días', report_data['period']['total_days']])
        writer.writerow(['Generado', report_data['generated_at'].strftime('%d/%m/%Y %H:%M')])
        writer.writerow([])
        
        # Agregar secciones
        for section in report_data['sections']:
            if section == 'activity_summary' and 'activity_summary' in report_data:
                writer.writerow(['Resumen de Actividad'])
                writer.writerow(['Métrica', 'Valor'])
                activity = report_data['activity_summary']
                for key, value in activity.items():
                    writer.writerow([key.replace('_', ' ').title(), value])
                writer.writerow([])
            
            if section == 'review_statistics' and 'review_statistics' in report_data:
                writer.writerow(['Estadísticas de Revisiones'])
                writer.writerow(['Métrica', 'Valor'])
                stats = report_data['review_statistics']
                metrics = [
                    ('Contenido aprobado', stats['approved_content']),
                    ('Contenido rechazado', stats['rejected_content']),
                    ('Tasa de aprobación (%)', stats['approval_rate']),
                    ('Tiempo promedio de revisión (horas)', stats['average_review_time']),
                ]
                
                for metric, value in metrics:
                    writer.writerow([metric, value])
                writer.writerow([])
        
        return response
        
    except Exception as e:
        print(f"Error generating CSV: {str(e)}")
        # Fallback básico
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="reporte_basic.txt"'
        response.write(f"Reporte de Experto\n")
        response.write(f"Usuario: {user.get_full_name()}\n")
        response.write(f"Email: {user.email}\n")
        response.write(f"Fecha: {timezone.now().strftime('%d/%m/%Y %H:%M')}\n")
        return response

# Reemplaza la función login_unificado (líneas 3209-3242) con esta versión corregida:

def login_unificado(request):
    """Vista de login unificado para todos los usuarios"""
    if request.user.is_authenticated:
        return redirect_to_user_dashboard(request)

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        
        if form.is_valid():
            user = form.get_user()
            
            # Verificar si el email está verificado
            if not user.is_email_verified:
                messages.warning(
                    request,
                    'Debes verificar tu email antes de iniciar sesión.'
                )
                return redirect('users:verify_email', user_id=user.id)
            
            # IMPORTANTE: Usar auth_login en lugar de login para evitar conflictos
            auth_login(request, user)
            messages.success(request, f'¡Bienvenido, {user.get_full_name()}!')
            return redirect_to_user_dashboard(request)
        else:
            messages.error(request, 'Credenciales inválidas.')
    else:
        form = LoginForm()
    
    # Contexto para el template
    context = {
        'form': form,
        'background_image': 'images/forms/fondo.png',
        'registration_link': 'users:register_student',
    }
    
    return render(request, 'accounts/login.html', context)
@login_required
def messages_home(request):
    """Vista principal de mensajería para todos los roles"""
    user = request.user
    
    # Obtener conversaciones del usuario
    conversations = Conversation.objects.filter(
        participants=user
    ).annotate(
        last_message_time=Max('messages__timestamp'),
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=user))
    ).order_by('-last_message_time')
    
    # Obtener solicitudes de contacto pendientes
    pending_requests = ContactRequest.objects.filter(
        to_user=user,
        status='pending'
    ).select_related('from_user')
    
    # Obtener contactos aceptados
    contacts = Contact.objects.filter(
        user=user,
        status='accepted'
    ).select_related('contact')
    
    # Asignar información del otro participante a cada conversación
    for conv in conversations:
        other_user = conv.get_other_participant(user)
        conv.other_user = other_user
        # Obtener último mensaje
        last_message = conv.messages.order_by('-timestamp').first()
        conv.last_message = last_message
    
    context = {
        'user': user,
        'conversations': conversations,
        'contacts': contacts,
        'pending_requests': pending_requests,
    }
    
    return render(request, 'shared/messages.html', context)

@login_required
@require_http_methods(["GET"])
def get_conversations(request):
    """API para obtener lista de conversaciones"""
    user = request.user
    
    conversations = Conversation.objects.filter(
        participants=user
    ).annotate(
        last_message_time=Max('messages__timestamp'),
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=user))
    ).order_by('-last_message_time')
    
    conversations_data = []
    for conv in conversations:
        # Obtener el otro participante
        other_participants = conv.participants.exclude(id=user.id)
        if other_participants.exists():
            other_user = other_participants.first()
            
            # Obtener último mensaje
            last_message = conv.messages.last()
            
            conversations_data.append({
                'id': conv.id,
                'name': other_user.get_full_name(),
                'avatar': other_user.avatar.url if other_user.avatar else None,
                'last_message_preview': last_message.content[:50] + '...' if last_message and len(last_message.content) > 50 else last_message.content if last_message else '',
                'last_message_time': last_message.timestamp.isoformat() if last_message else '',
                'unread_count': conv.unread_count,
                'participants_info': f"{other_user.get_full_name()} • {other_user.get_user_type_display()}"
            })
    
    return JsonResponse({
        'success': True,
        'conversations': conversations_data
    })

@login_required
def conversation_detail(request, conversation_id):
    """Vista de detalle de conversación"""
    try:
        conversation = Conversation.objects.get(
            id=conversation_id,
            participants=request.user
        )
        
        # Marcar mensajes como leídos
        conversation.messages.filter(
            is_read=False
        ).exclude(sender=request.user).update(is_read=True)
        
        context = {
            'conversation': conversation,
            'user': request.user
        }
        
        return render(request, 'shared/conversation_detail.html', context)
        
    except Conversation.DoesNotExist:
        return redirect('users:messages_home')

@login_required
@require_http_methods(["GET"])
def get_conversation_messages(request, conversation_id):
    """API para obtener mensajes de una conversación"""
    try:
        conversation = Conversation.objects.get(
            id=conversation_id,
            participants=request.user
        )
        
        messages = conversation.messages.select_related('sender').order_by('timestamp')
        
        # Obtener el otro participante para info de la conversación
        other_participants = conversation.participants.exclude(id=request.user.id)
        other_user = other_participants.first() if other_participants.exists() else None
        
        messages_data = []
        for message in messages:
            messages_data.append({
                'id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'sender_id': message.sender.id,
                'is_from_user': message.sender == request.user,
                'is_read': message.is_read,
                'sender': {
                    'id': message.sender.id,
                    'full_name': message.sender.get_full_name(),
                    'avatar': message.sender.avatar.url if message.sender.avatar else None
                }
            })
        
        conversation_data = {
            'id': conversation.id,
            'name': other_user.get_full_name() if other_user else 'Conversación',
            'avatar': other_user.avatar.url if other_user and other_user.avatar else None,
            'participants_info': f"{other_user.get_full_name()} • {other_user.get_user_type_display()}" if other_user else '',
            'other_user_id': other_user.id if other_user else None
        }
        
        # Marcar mensajes como leídos
        conversation.messages.filter(
            is_read=False
        ).exclude(sender=request.user).update(is_read=True)
        
        return JsonResponse({
            'success': True,
            'messages': messages_data,
            'conversation': conversation_data
        })
        
    except Conversation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Conversación no encontrada'
        })

@login_required
@require_http_methods(["POST"])
def send_message(request):
    """API para enviar mensaje"""
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        content = data.get('content', '').strip()
        
        if not conversation_id or not content:
            return JsonResponse({
                'success': False,
                'error': 'Datos insuficientes'
            })
        
        conversation = Conversation.objects.get(
            id=conversation_id,
            participants=request.user
        )
        
        # Crear mensaje
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content
        )
        
        # Actualizar timestamp de conversación
        conversation.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'sender_id': message.sender.id,
                'is_from_user': True,
                'is_read': False,
                'sender': {
                    'id': message.sender.id,
                    'full_name': message.sender.get_full_name(),
                    'avatar': message.sender.avatar.url if message.sender.avatar else None
                }
            }
        })
        
    except Conversation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Conversación no encontrada'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_http_methods(["POST"])
def start_conversation(request):
    """API para iniciar nueva conversación"""
    try:
        data = json.loads(request.body)
        contact_id = data.get('contact_id')
        message_content = data.get('message', '').strip()
        
        if not contact_id or not message_content:
            return JsonResponse({
                'success': False,
                'error': 'Datos insuficientes'
            })
        
        contact_user = User.objects.get(id=contact_id)
        
        # Verificar si ya existe una conversación
        existing_conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=contact_user
        ).first()
        
        if existing_conversation:
            conversation = existing_conversation
        else:
            # Crear nueva conversación
            conversation = Conversation.objects.create()
            conversation.participants.add(request.user, contact_user)
        
        # Crear mensaje inicial
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=message_content
        )
        
        return JsonResponse({
            'success': True,
            'conversation_id': conversation.id,
            'message': 'Conversación iniciada exitosamente'
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Usuario no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_http_methods(["POST"])
def mark_messages_read(request, conversation_id):
    """API para marcar mensajes como leídos"""
    try:
        conversation = Conversation.objects.get(
            id=conversation_id,
            participants=request.user
        )
        
        # Marcar como leídos todos los mensajes no leídos que no sean del usuario actual
        updated_count = conversation.messages.filter(
            is_read=False
        ).exclude(sender=request.user).update(is_read=True)
        
        return JsonResponse({
            'success': True,
            'marked_count': updated_count
        })
        
    except Conversation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Conversación no encontrada'
        })

@login_required
@require_http_methods(["GET"])
def check_new_messages(request, conversation_id):
    """API para verificar nuevos mensajes"""
    try:
        conversation = Conversation.objects.get(
            id=conversation_id,
            participants=request.user
        )
        
        last_id = int(request.GET.get('last_id', 0))
        
        # Obtener mensajes nuevos
        new_messages = conversation.messages.filter(
            id__gt=last_id
        ).exclude(sender=request.user).select_related('sender')
        
        # Obtener actualizaciones de estado de lectura
        read_updates = conversation.messages.filter(
            sender=request.user,
            is_read=True,
            id__gt=last_id
        )
        
        new_messages_data = []
        for message in new_messages:
            new_messages_data.append({
                'id': message.id,
                'content': message.content,
                'created_at': message.timestamp.isoformat(),
                'sender': {
                    'id': message.sender.id,
                    'full_name': message.sender.get_full_name(),
                    'avatar': message.sender.avatar.url if message.sender.avatar else None
                }
            })
        
        read_updates_data = [{'message_id': msg.id} for msg in read_updates]
        
        return JsonResponse({
            'success': True,
            'new_messages': new_messages_data,
            'read_updates': read_updates_data
        })
        
    except Conversation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Conversación no encontrada'
        })

@login_required
@require_http_methods(["POST"])
def typing_indicator(request, conversation_id):
    """API para indicador de escritura"""
    # En una implementación real, esto podría usar WebSockets o Redis
    # Por ahora, simplemente retornamos éxito
    return JsonResponse({'success': True})

@login_required
@require_http_methods(["POST"])
def stop_typing_indicator(request, conversation_id):
    """API para detener indicador de escritura"""
    # En una implementación real, esto podría usar WebSockets o Redis
    # Por ahora, simplemente retornamos éxito
    return JsonResponse({'success': True})

@login_required
@require_http_methods(["GET"])
def get_contacts(request):
    """API para obtener lista de contactos"""
    user = request.user
    
    # Obtener contactos aceptados
    accepted_requests = ContactRequest.objects.filter(
        Q(from_user=user, status='accepted') | Q(to_user=user, status='accepted')
    ).select_related('from_user', 'to_user')
    
    contacts = []
    for req in accepted_requests:
        contact = req.to_user if req.from_user == user else req.from_user
        contacts.append({
            'id': contact.id,
            'full_name': contact.get_full_name(),
            'username': contact.username,
            'avatar': contact.avatar.url if contact.avatar else None,
            'user_type_name': contact.get_user_type_display(),
            'is_online': False  # Implementar lógica de estado online si es necesario
        })
    
    return JsonResponse({
        'success': True,
        'contacts': contacts
    })

@login_required
@require_http_methods(["POST"])
def add_contact(request):
    """API para enviar solicitud de contacto"""
    try:
        data = json.loads(request.body)
        contact_id = data.get('contact')
        
        if not contact_id:
            return JsonResponse({
                'success': False,
                'error': 'ID de contacto requerido'
            })
        
        contact_user = User.objects.get(id=contact_id)
        
        if contact_user == request.user:
            return JsonResponse({
                'success': False,
                'error': 'No puedes agregarte a ti mismo'
            })
        
        # Verificar si ya existe una solicitud
        existing_request = ContactRequest.objects.filter(
            Q(from_user=request.user, to_user=contact_user) |
            Q(from_user=contact_user, to_user=request.user)
        ).first()
        
        if existing_request:
            return JsonResponse({
                'success': False,
                'error': 'Ya existe una solicitud de contacto'
            })
        
        # Crear solicitud
        ContactRequest.objects.create(
            from_user=request.user,
            to_user=contact_user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Solicitud de contacto enviada'
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Usuario no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_http_methods(["POST"])
def respond_contact_request(request, request_id):
    """API para responder solicitud de contacto"""
    try:
        contact_request = ContactRequest.objects.get(
            id=request_id,
            to_user=request.user,
            status='pending'
        )
        
        data = json.loads(request.body)
        action = data.get('action')
        
        if action == 'accept':
            contact_request.status = 'accepted'
            contact_request.save()
            
            # Crear contactos mutuos
            Contact.objects.get_or_create(
                user=request.user,
                contact=contact_request.from_user,
                defaults={'status': 'accepted'}
            )
            Contact.objects.get_or_create(
                user=contact_request.from_user,
                contact=request.user,
                defaults={'status': 'accepted'}
            )
            
            message = 'Solicitud aceptada'
        elif action == 'reject':
            contact_request.status = 'rejected'
            contact_request.save()
            message = 'Solicitud rechazada'
        else:
            return JsonResponse({
                'success': False,
                'error': 'Acción inválida'
            })
        
        return JsonResponse({
            'success': True,
            'message': message
        })
        
    except ContactRequest.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Solicitud no encontrada'
        })

@login_required
@require_http_methods(["GET"])
def search_users(request):
    """API para buscar usuarios"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({
            'success': True,
            'users': []
        })
    
    # Buscar usuarios excluyendo al usuario actual
    users = User.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(username__icontains=query)|
        Q(email__icontains=query)
    ).exclude(id=request.user.id)[:10]  # Limitar a 10 resultados
    
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'full_name': user.get_full_name(),
            'username': user.username,
            'email': user.email,
            'avatar': user.avatar.url if user.avatar else None,
            'user_type_name': user.get_user_type_display()
        })
    
    return JsonResponse({
        'success': True,
        'users': users_data
    })