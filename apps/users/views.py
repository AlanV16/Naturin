from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages 
from django.contrib.auth import login, authenticate
from .models import User, Event, Message, Conversation, ConversationMessage
from .forms import StudentRegisterForm
from django.contrib.auth.decorators import login_required   
from .forms import LoginForm, TeacherRegisterForm, ParentRegisterForm
import logging
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
import calendar
import os
from django.urls import reverse
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from validate_email import validate_email
from django.core.paginator import Paginator
from django.contrib.auth import logout
import random
import string
from django.db import transaction
from apps.educational_games.gamification.models import Classroom, ClassroomStudent, Activities, Levels
from .utils import generate_unique_class_code
from .utils import send_verification_email, send_welcome_email
# Import de modelos adicionales
from .models import (
    Course, Subject, Enrollment, Assignment, AssignmentSubmission, 
    Achievement, StudentAchievement, Event,
    Message, Conversation, ConversationMessage, User
)
# Importa Notification desde la nueva app de gamificación
from apps.educational_games.gamification.models import Notification

from .forms import (
    LoginForm, StudentRegisterForm, TeacherRegisterForm, ParentRegisterForm, 
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
    4: {  # Admin
        'name': 'Administrador',
        'background': 'images/forms/fondo_admin.png',
        'registration_url': None,  # Los admin no se registran públicamente
        'dashboard_url': 'users:dashboard_admin'
    }
}
# ===== VISTAS DE AUTENTICACIÓN =====

def login_unificado(request):
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
            
            login(request, user)
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
    
    if user.user_type == 1:  # Estudiante
        return redirect('users:dashboard_student', user_id=user.id)
    elif user.user_type == 2:  # Docente
        return redirect('users:dashboard_teacher', user_id=user.id)
    elif user.user_type == 3:  # Padre
        return redirect('users:dashboard_parent', user_id=user.id)
    elif user.user_type == 4:  # Admin
        return redirect('users:dashboard_admin', user_id=user.id)
    else:
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
        # Obtener las clases del estudiante usando el modelo correcto
        from apps.educational_games.gamification.models import ClassroomStudent, Classroom
        inscripciones = ClassroomStudent.objects.filter(student=user).select_related('classroom', 'classroom__teacher')
        courses = []
        
        # Procesar inscripciones de forma segura
        for inscripcion in inscripciones:
            try:
                courses.append(inscripcion.classroom)
            except Exception as e:
                print(f"Error procesando inscripción {inscripcion.id}: {e}")
                continue
                
    except Exception as e:
        print(f"Error obteniendo inscripciones: {e}")
        inscripciones = []
        courses = []
    
    # Estadísticas generales with valores por defecto
    total_courses = len(courses)
    active_courses = total_courses  # Todas las clases están activas por defecto
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
            # Progreso general (simulado para clases)
            general_progress = 75  # Progreso simulado
            
            # Cursos para mostrar en el dashboard (máximo 3)
            for inscripcion in inscripciones[:3]:
                try:
                    aula = inscripcion.classroom
                    teacher_name = "Sin asignar"
                    try:
                        teacher_name = aula.teacher.get_full_name() if aula.teacher else "Sin asignar"
                    except:
                        pass
                    
                    icon = "book"
                    
                    course_details.append({
                        'id': aula.IDaula,
                        'name': aula.NombreAula,
                        'teacher': teacher_name,
                        'progress': 75,  # Progreso simulado
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
                title='¡Bienvenido a NaturIn!',
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
    
    # Cálculos de rendimiento académico (simulado para clases)
    try:
        # Para clases, usamos datos simulados
        average_grade = 8.5
        completion_percentage = 75
        grade_letter = 'B+'
        user_ranking = 3
        
    except Exception as e:
        print(f"Error calculando rendimiento: {e}")
        average_grade = 0
        completion_percentage = 0
        grade_letter = 'N/A'
        user_ranking = 'N/A'
    
    # Datos para el gráfico de rendimiento
    performance_data = {
        'completed': min(completion_percentage, 100),
        'pending': max(100 - completion_percentage, 0),
        'average_grade': round(average_grade, 1),
        'grade_letter': grade_letter,
        'ranking': user_ranking,
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
    
    return render(request, 'dashboards/dashboard_student.html', context)

# ================== VISTAS PARA RESET DE CONTRASEÑA ==================

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

@login_required
def dashboard_teacher(request, user_id):
    """Dashboard principal para docentes"""
    user = request.user
    
    # Verificar que es docente
    if user.user_type != 2:
        return redirect('users:dashboard_student')
    
    # Obtener todas las clases del docente
    teacher_classrooms = Classroom.objects.filter(teacher=user)
    total_students = ClassroomStudent.objects.filter(classroom__in=teacher_classrooms).count()
    active_classrooms = teacher_classrooms.filter(status='active').count() if hasattr(Classroom, 'status') else teacher_classrooms.count()
    
    # Tareas recientes pendientes de calificar (placeholder)
    pending_submissions = []
    pending_count = 0
    
    # Actividades recientes (placeholder)
    recent_activities = []
    
    # Logros recientes
    recent_achievements = Achievement.objects.filter(user=user).order_by('-earned_at')[:5]
    
    # Preparar estadísticas de clases para el template
    classroom_stats = []
    for classroom in teacher_classrooms:
        students_count = ClassroomStudent.objects.filter(classroom=classroom).count()
        classroom_stats.append({
            'classroom': classroom,
            'students_count': students_count,
            'avg_grade': 0,  # Placeholder
            'assignments_count': 0,  # Placeholder
            'pending_submissions': 0,  # Placeholder
            'status': getattr(classroom, 'status', 'active')
        })
    
    context = {
        'user': user,
        'active_courses': active_classrooms,
        'total_students': total_students,
        'pending_count': pending_count,
        'recent_achievements': recent_achievements,
        'course_stats': classroom_stats,
        'pending_submissions': pending_submissions,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'dashboards/dashboard_teacher.html', context)

@login_required
def dashboard_parent(request, user_id):
    logging.debug("Entrando a dashboard_parent")
    print("Entrando a dashboard_parent")
    user = get_object_or_404(User, id=user_id)
    context = {
        'user': user,
        # Puedes agregar más datos al contexto si es necesario
    }
    return render(request, 'dashboards/dashboard_parent.html', context)

@login_required
def dashboard_admin(request, user_id):
    logging.debug("Entrando a dashboard_admin")
    print("Entrando a dashboard_admin")  # para la consola de runserver
    user = get_object_or_404(User, id=user_id)
    context = {
        'user': user,
        # Puedes agregar más datos al contexto si es necesario
    }
    return render(request, 'dashboards/dashboard_admin.html', context)

def get_user_dashboard_url(user):
    """
    Función auxiliar para obtener la URL del dashboard según el tipo de usuario
    """
    if user.user_type in USER_TYPE_CONFIG:
        dashboard_url = USER_TYPE_CONFIG[user.user_type]['dashboard_url']
        return reverse(dashboard_url, kwargs={'user_id': user.id})
    return reverse('users:login')



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
        assignmentsubmission__student=user
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
def student_calendar(request):
    """Vista para mostrar el calendario del estudiante"""
    user = request.user
    
    # Obtener el mes y año actual o desde parámetros GET
    today = timezone.now().date()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))
    
    # Crear fechas de inicio y fin del mes
    first_day = datetime(year, month, 1).date()
    if month == 12:
        last_day = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)
    
    # Obtener cursos del estudiante
    user_courses = Course.objects.filter(enrollment__student=user).distinct()
    
    # Obtener eventos del mes
    events = []
    
    # 1. Tareas con fecha de vencimiento
    assignments = Assignment.objects.filter(
        course__in=user_courses,
        due_date__date__range=[first_day, last_day]
    ).select_related('course')
    
    for assignment in assignments:
        # Verificar si ya fue entregada
        is_submitted = AssignmentSubmission.objects.filter(
            student=user,
            assignment=assignment
        ).exists()
        
        events.append({
            'id': f'assignment_{assignment.id}',
            'title': assignment.title,
            'date': assignment.due_date.date(),
            'time': assignment.due_date.time(),
            'type': 'assignment',
            'course': assignment.course.name,
            'description': assignment.description,
            'status': 'submitted' if is_submitted else 'pending',
            'icon': 'clipboard-check',
            'color': 'success' if is_submitted else 'warning'
        })
    
    # 2. Clases programadas (si tienes un modelo Schedule)
    try:
        scheduled_classes = Event.objects.filter(
            course__in=user_courses,
            start_date__date__range=[first_day, last_day]
        ).select_related('course')
        
        for class_event in scheduled_classes:
            events.append({
                'id': f'class_{class_event.id}',
                'title': class_event.title,
                'date': class_event.start_date.date(),
                'time': class_event.start_date.time(),
                'type': 'class',
                'course': class_event.course.name,
                'description': class_event.description,
                'status': 'scheduled',
                'icon': 'camera-video',
                'color': 'primary'
            })
    except:
        # Si no existe el modelo Event aún
        pass
    
    # Organizar eventos por fecha
    events_by_date = {}
    for event in events:
        date_str = event['date'].strftime('%Y-%m-%d')
        if date_str not in events_by_date:
            events_by_date[date_str] = []
        events_by_date[date_str].append(event)
    
    # Generar estructura del calendario
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    
    # Navegación de meses
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    # Estadísticas del mes
    total_assignments = len([e for e in events if e['type'] == 'assignment'])
    pending_assignments = len([e for e in events if e['type'] == 'assignment' and e['status'] == 'pending'])
    total_classes = len([e for e in events if e['type'] == 'class'])
    total_exams = len([e for e in events if e['type'] == 'exam'])
    
    context = {
        'user': user,
        'calendar_data': cal,
        'month': month,
        'year': year,
        'month_name': month_name,
        'today': today,
        'events_by_date': events_by_date,
        'events': events,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'total_assignments': total_assignments,
        'pending_assignments': pending_assignments,
        'total_classes': total_classes,
        'total_exams': total_exams,
    }
    
    return render(request, 'students/calendar.html', context)

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
def student_messages(request):
    """Vista para mostrar los mensajes del estudiante con datos reales"""
    user = request.user
    if user.user_type != 1:
        return redirect('users:dashboard_student')
    
    # Obtener mensajes directos recibidos y enviados
    direct_messages = Message.objects.filter(
        Q(sender=user) | Q(recipient=user)
    ).select_related('sender', 'recipient').order_by('-created_at')
    
    # Obtener conversaciones del usuario
    conversations = Conversation.objects.filter(participants=user).order_by('-updated_at')
    
    # Contar mensajes no leídos
    unread_direct = Message.objects.filter(recipient=user, is_read=False).count()
    unread_conversations = 0
    for conv in conversations:
        # Contar mensajes no leídos en conversaciones (excluyendo los del usuario actual)
        unread_count = conv.conversation_messages.filter(
            is_read=False
        ).exclude(sender=user).count()
        unread_conversations += unread_count
    
    total_unread = unread_direct + unread_conversations
    
    # Obtener profesores de los cursos del estudiante para poder enviar mensajes
    student_courses = Course.objects.filter(enrollment__student=user)
    teachers = User.objects.filter(
        taught_courses__enrollment__student=user,
        user_type=2
    ).distinct().order_by('last_name', 'first_name')
    
    context = {
        'user': user,
        'direct_messages': direct_messages[:20],  # Solo los 20 más recientes
        'conversations': conversations,
        'total_unread': total_unread,
        'teachers': teachers,
        'student_courses': student_courses,
    }
    return render(request, 'students/messages.html', context)

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
def teacher_calendar(request):
    """Vista para mostrar el calendario del docente con eventos reales"""
    user = request.user
    if user.user_type != 2:
        return redirect('users:dashboard_student')
    
    # Obtener fecha actual o la solicitada
    today = timezone.now().date()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))
    
    # Crear fecha del mes solicitado
    month_start = datetime(year, month, 1).date()
    if month == 12:
        month_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        month_end = datetime(year, month + 1, 1).date() - timedelta(days=1)
    
    # Obtener eventos del mes para los cursos del profesor
    events = Event.objects.filter(
        course__teacher=user,
        start_date__date__gte=month_start,
        start_date__date__lte=month_end
    ).select_related('course').order_by('start_date')
    
    # Si no hay eventos, crear algunos de ejemplo (opcional para demo)
    if not events.exists() and Course.objects.filter(teacher=user).exists():
        # Solo crear eventos de ejemplo si el profesor tiene cursos pero no eventos
        sample_course = Course.objects.filter(teacher=user).first()
        if sample_course:
            # Crear evento de ejemplo para hoy
            today_datetime = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
            Event.objects.get_or_create(
                title="Clase de Introducción",
                course=sample_course,
                event_type='class',
                start_date=today_datetime,
                end_date=today_datetime.replace(hour=11),
                defaults={
                    'description': 'Clase introductoria del curso',
                    'location': 'Aula Virtual'
                }
            )
            
            # Refrescar la consulta
            events = Event.objects.filter(
                course__teacher=user,
                start_date__date__gte=month_start,
                start_date__date__lte=month_end
            ).select_related('course').order_by('start_date')
    
    # Obtener próximos eventos (los siguientes 5)
    upcoming_events = Event.objects.filter(
        course__teacher=user,
        start_date__gte=timezone.now()
    ).select_related('course').order_by('start_date')[:5]
    
    # Crear diccionario de eventos por día
    events_by_day = {}
    for event in events:
        day = event.start_date.date().day
        if day not in events_by_day:
            events_by_day[day] = []
        events_by_day[day].append(event)
    
    # Obtener información del calendario
    calendar_obj = calendar.Calendar(firstweekday=0)  # Lunes como primer día
    month_days = calendar_obj.monthdayscalendar(year, month)
    month_name = calendar.month_name[month]
    
    # Navegación de meses
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    context = {
        'user': user,
        'month': month,
        'year': year,
        'month_name': month_name,
        'month_days': month_days,
        'events_by_day': events_by_day,
        'upcoming_events': upcoming_events,
        'today': today,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'teacher_courses': Course.objects.filter(teacher=user),  # Agregar cursos del profesor
    }
    return render(request, 'teachers/calendar.html', context)

@login_required
def teacher_messages(request):
    """Vista para mostrar los mensajes del docente con datos reales"""
    user = request.user
    if user.user_type != 2:
        return redirect('users:dashboard_student')
    
    # Obtener todas las conversaciones del usuario
    conversations = Conversation.objects.filter(participants=user).order_by('-updated_at')
    
    # Obtener mensajes directos recibidos (sistema antiguo)
    direct_messages = Message.objects.filter(
        Q(sender=user) | Q(recipient=user)
    ).select_related('sender', 'recipient').order_by('-created_at')
    
    # Contar mensajes no leídos
    unread_conversations = 0
    for conv in conversations:
        # Contar mensajes no leídos en conversaciones (excluyendo los del usuario actual)
        unread_count = conv.conversation_messages.filter(
            is_read=False
        ).exclude(sender=user).count()
        unread_conversations += unread_count
    
    unread_direct = Message.objects.filter(recipient=user, is_read=False).count()
    total_unread = unread_conversations + unread_direct
    
    # Obtener estudiantes de los cursos del profesor para poder enviar mensajes
    teacher_courses = Course.objects.filter(teacher=user)
    students = User.objects.filter(
        enrollment__course__teacher=user,
        user_type=1
    ).distinct().order_by('last_name', 'first_name')
    
    context = {
        'user': user,
        'conversations': conversations,
        'direct_messages': direct_messages[:10],  # Solo los 10 más recientes
        'total_unread': total_unread,
        'students': students,
        'teacher_courses': teacher_courses,
    }
    return render(request, 'teachers/messages.html', context)

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



# ===== OTRAS VISTAS =====

@login_required
def course_detail(request, course_id):
    """Vista detallada de un curso - redirige a la vista de clase correspondiente"""
    try:
        from apps.educational_games.gamification.models import Classroom, ClassroomStudent
        classroom = Classroom.objects.get(id=course_id)
        
        # Verificar si el usuario está inscrito
        is_enrolled = ClassroomStudent.objects.filter(
            student=request.user, 
            classroom=classroom
        ).exists()
        
        if request.user.user_type == 2:  # Docente
            if classroom.teacher == request.user:
                return redirect('users:class_teacher', class_id=course_id)
            else:
                messages.error(request, 'No tienes permisos para acceder a esta clase')
                return redirect('users:dashboard_teacher', user_id=request.user.id)
        else:  # Estudiante
            if is_enrolled:
                return redirect('users:class_student', class_id=course_id)
            else:
                messages.error(request, 'No estás inscrito en esta clase')
                return redirect('users:dashboard_student', user_id=request.user.id)
                
    except Classroom.DoesNotExist:
        messages.error(request, 'Curso no encontrado')
        return redirect('users:dashboard_student', user_id=request.user.id)

def generate_unique_class_code():
    """Genera un código único para el aula de 6 caracteres alfanuméricos"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Classroom.objects.filter(code=code).exists():
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
                'completion_rate': (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0,
                'average_grade': round(average_grade, 2)
            },
            'courses': courses_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def user_calendar(request):
    """Vista básica de calendario de usuario"""
    return render(request, 'users/user_calendar.html')


# ============================================================================
# AULAS VIRTUALES
# ============================================================================

@login_required
def join_class(request):
    """Vista para que un estudiante se una a una clase usando código"""
    if request.user.user_type != 1:  # Solo estudiantes
        messages.error(request, 'Solo los estudiantes pueden unirse a clases.')
        return redirect('users:dashboard_student', user_id=request.user.id)
    
    if request.method == 'POST':
        # Aceptar tanto 'class_code' como 'course_code' para compatibilidad
        class_code = request.POST.get('class_code') or request.POST.get('course_code')
        
        if not class_code:
            messages.error(request, 'Por favor ingresa el código de la clase.')
            return redirect('users:dashboard_student', user_id=request.user.id)
        
        try:
            # Buscar la clase solo por código
            classroom = Classroom.objects.get(code=class_code)
            
            # Verificar si el estudiante ya está en la clase
            if ClassroomStudent.objects.filter(classroom=classroom, student=request.user).exists():
                messages.warning(request, 'Ya estás inscrito en esta clase.')
                return redirect('users:dashboard_student', user_id=request.user.id)
            
            # Inscribir al estudiante
            ClassroomStudent.objects.create(
                classroom=classroom,
                student=request.user,
                joined_at=timezone.now()
            )
            
            messages.success(request, f'Te has unido exitosamente a la clase "{classroom.name}"')
            return redirect('users:class_student', class_id=classroom.id)
            
        except Classroom.DoesNotExist:
            messages.error(request, 'No se encontró la clase con el código proporcionado.')
        except Exception as e:
            messages.error(request, 'Error al unirse a la clase.')
    
    # Si es GET, redirigir al dashboard
    return redirect('users:dashboard_student', user_id=request.user.id)

@login_required
def create_class(request):
    """Crear una nueva clase"""
    if request.user.user_type != 2:  # Solo docentes pueden crear clases
        messages.error(request, 'Solo los docentes pueden crear clases.')
        return redirect('users:dashboard_teacher')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Generar código único automáticamente
                code = generate_unique_class_code()
                
                # Validar campos requeridos
                required_fields = ['class_name', 'grade', 'section']
                for field in required_fields:
                    if not request.POST.get(field):
                        messages.error(request, f'El campo {field} es requerido.')
                        return redirect('users:create_class')
                
                # Crear la clase
                classroom = Classroom.objects.create(
                    name=request.POST.get('class_name'),
                    description=request.POST.get('description', ''),
                    grade=request.POST.get('grade'),
                    section=request.POST.get('section'),
                    code=code,
                    teacher=request.user,
                    created_at=timezone.now()
                )
                
                # Asignar actividades seleccionadas
                selected_activities = request.POST.getlist('activities')
                for activity_id in selected_activities:
                    try:
                        activity = Activities.objects.get(IDactividad=activity_id)
                        # Crear relación entre clase y actividad
                        Activities.objects.create(
                            Titulo=f"Actividad - {activity.Titulo}",
                            Instrucciones=activity.Instrucciones,
                            IDtipoActividad=activity.IDtipoActividad,
                            IDficha=activity.IDficha,
                            IDaula=classroom
                        )
                    except Activities.DoesNotExist:
                        continue
                
                messages.success(request, f'Clase "{classroom.name}" creada exitosamente. Código de clase: {code}')
                return redirect('users:class_teacher', class_id=classroom.id)
                
        except Exception as e:
            messages.error(request, f'Error al crear la clase: {str(e)}')
    
    # Obtener actividades disponibles (sin filtrar por estado ya que no existe ese campo)
    activities = Activities.objects.all()
    
    context = {
        'activities': activities,
        'grades': ['Primero', 'Segundo'],
        'sections': ['A', 'B', 'C', 'D', 'E'],
    }
    
    return render(request, 'class/create_class.html', context)

@login_required
def class_student(request, class_id):
    classroom = get_object_or_404(Classroom, id=class_id)
    if not ClassroomStudent.objects.filter(classroom=classroom, student=request.user).exists():
        messages.error(request, 'No tienes acceso a esta clase.')
        return redirect('users:dashboard_student', user_id=request.user.id)
    activities = Activities.objects.all()[:5]
    try:
        progress = Levels.objects.get(IDusuario=request.user)
    except Levels.DoesNotExist:
        progress = None
    chat_messages = []
    context = {
        'class': classroom,
        'activities': activities,
        'progress': progress,
        'chat_messages': chat_messages,
        'theoretical_content': [],
        'user': request.user,
    }
    return render(request, 'class/class_student.html', context)

@login_required
def class_teacher(request, class_id):
    """Vista de clase para docentes con funcionalidades integradas de gamificación"""
    try:
        classroom = get_object_or_404(Classroom, id=class_id)
        
        # Verificar que el usuario es el docente de la clase
        if classroom.teacher != request.user:
            messages.error(request, 'No tienes permisos para acceder a esta clase.')
            return redirect('users:dashboard_teacher', user_id=request.user.id)
            
    except Classroom.DoesNotExist:
        messages.error(request, f'La clase con ID {class_id} no existe.')
        return redirect('users:dashboard_teacher', user_id=request.user.id)
    except Exception as e:
        messages.error(request, f'Error al acceder a la clase: {str(e)}')
        return redirect('users:dashboard_teacher', user_id=request.user.id)
    
    if request.method == 'POST':
        # Manejar mensajes del chat
        if 'chat_message' in request.POST:
            message = request.POST.get('chat_message')
            if message.strip():
                # Crear o obtener conversación del aula
                conversation, created = Conversation.objects.get_or_create(
                    id=classroom.id  # Usar el ID del aula como identificador único
                )
                # Agregar participantes si es nueva
                if created:
                    conversation.participants.add(request.user)
                    for student in students:
                        conversation.participants.add(student.student)
                ConversationMessage.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=message
                )
                messages.success(request, 'Mensaje enviado.')
        
        # Manejar recompensas a estudiantes
        if 'reward_student' in request.POST:
            student_id = request.POST.get('student_id')
            points = int(request.POST.get('reward_student'))
            reason = request.POST.get('reward_reason', 'Participación destacada')
            
            try:
                with transaction.atomic():
                    student = User.objects.get(id=student_id)
                    nivel, created = Levels.objects.get_or_create(IDusuario=student)
                    nivel.puntos_acumulados += points
                    nivel.actualizar_nivel()
                    nivel.save()
                    
                    # Crear notificación para el estudiante
                    Notification.objects.create(
                        recipient=student,
                        title="¡Has recibido puntos!",
                        message=f"El profesor te ha otorgado {points} puntos por: {reason}",
                        notification_type="achievement_unlocked"
                    )
                    
                    messages.success(request, f'Se otorgaron {points} puntos al estudiante.')
            except Exception as e:
                messages.error(request, f'Error al otorgar puntos: {str(e)}')
    
    # Obtener estudiantes inscritos con su información de progreso
    students = ClassroomStudent.objects.filter(classroom=classroom).select_related('student')
    
    # Obtener actividades específicas de la clase
    activities = Activities.objects.filter(IDaula=classroom).select_related('IDtipoActividad')
    
    # Obtener progreso de estudiantes eficientemente
    progress_list = []
    student_ids = [student.student.id for student in students]
    niveles = {nivel.IDusuario_id: nivel for nivel in Levels.objects.filter(IDusuario_id__in=student_ids)}
    
    for student in students:
        nivel = niveles.get(student.student.id)
        progress_list.append({
            'user': student.student,
            'points': nivel.puntos_acumulados if nivel else 0,
            'level': nivel.nivel_actual if nivel else 1,
            'next_level_points': nivel.puntos_siguiente_nivel if nivel else 100
        })
    
    # Ordenar por puntos
    progress_list.sort(key=lambda x: x['points'], reverse=True)
    
    # Obtener mensajes del chat
    try:
        # Buscar conversación por participantes (docente y estudiantes de la clase)
        conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants__in=students.values_list('student', flat=True)
        ).first()
        
        if conversation:
            chat_messages = ConversationMessage.objects.filter(conversation=conversation).order_by('-created_at')[:50]
        else:
            chat_messages = []
    except Exception:
        chat_messages = []
    
    context = {
        'class': classroom,
        'students': students,
        'activities': activities,
        'progress_list': progress_list,
        'chat_messages': chat_messages,
        'reward_reasons': [
            'Participación destacada',
            'Ayuda a compañeros',
            'Completar actividad',
            'Respuesta correcta',
            'Proyecto especial'
        ]
    }
    
    return render(request, 'class/class_teacher.html', context)

@login_required
def play_game(request, class_id):
    """Vista para jugar juegos educativos"""
    classroom = get_object_or_404(Classroom, id=class_id)
    
    # Verificar acceso
    if request.user.user_type == 1:  # Estudiante
        if not ClassroomStudent.objects.filter(classroom=classroom, student=request.user).exists():
            messages.error(request, 'No tienes acceso a esta clase.')
            return redirect('users:dashboard_student')
    elif request.user.user_type == 2:  # Docente
        if classroom.teacher != request.user:
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
        code = generate_unique_class_code()
        return JsonResponse({'code': code})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def create_class_api(request):
    """Vista API para crear una nueva clase virtual con actividades iniciales"""
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
            activities_json = request.POST.get('activities', '[]')
            
            # Validar campos requeridos
            if not all([course_name, course_code, grade, section]):
                return JsonResponse({'error': 'Faltan campos requeridos'}, status=400)
            
            # Verificar que el código sea único
            if Classroom.objects.filter(code=course_code).exists():
                return JsonResponse({'error': 'El código de la clase ya existe'}, status=400)
            
            # Crear el aula
            classroom = Classroom.objects.create(
                name=course_name,
                code=course_code,
                grade=grade,
                section=section,
                description=description,
                teacher=request.user,
                created_at=timezone.now()
            )
            
            # Procesar actividades iniciales si las hay
            activities_created = []
            if activities_json and activities_json != '[]':
                try:
                    import json
                    activities = json.loads(activities_json)
                    
                    for activity in activities:
                        activity_type = activity.get('type')
                        activity_title = activity.get('title')
                        
                        if activity_type == 'test':
                            # Crear test básico
                            from apps.educational_games.gamification.models import Test, ActivityType
                            
                            # Obtener tipo de actividad para tests
                            tipo_actividad, created = ActivityType.objects.get_or_create(
                                TipoActividad='Test'
                            )
                            
                            # Crear actividad
                            actividad = Activities.objects.create(
                                Titulo=activity_title,
                                Instrucciones=f'Test: {activity_title}',
                                IDtipoActividad=tipo_actividad,
                                IDficha=0,  # Placeholder
                                IDaula=classroom
                            )
                            
                            # Crear test
                            test = Test.objects.create(
                                titulo=activity_title,
                                descripcion=f'Test creado para {classroom.name}',
                                IDaula=classroom,
                                IDdocente=request.user,
                                fecha_inicio=timezone.now(),
                                fecha_fin=timezone.now() + timedelta(days=30),
                                tiempo_limite=30,
                                puntos_por_pregunta=10,
                                activo=True
                            )
                            
                            activities_created.append({
                                'type': 'test',
                                'title': activity_title,
                                'id': test.IDtest
                            })
                            
                        elif activity_type == 'assignment':
                            # Crear tarea básica - omitir por ahora ya que no tenemos Course model
                            # from .models import Assignment
                            # assignment = Assignment.objects.create(
                            #     title=activity_title,
                            #     description=f'Tarea: {activity_title}',
                            #     course=None,  # No tenemos Course model, usar None por ahora
                            #     due_date=timezone.now() + timedelta(days=7),
                            #     points=100
                            # )
                            
                            activities_created.append({
                                'type': 'assignment',
                                'title': activity_title,
                                'id': 0  # Placeholder
                            })
                            
                        elif activity_type == 'multimedia':
                            # Crear recurso multimedia básico - omitir por ahora por problemas de campos
                            # from apps.multimedia.models import MultimediaCard
                            # from apps.common.models import Category
                            
                            # # Obtener categoría por defecto
                            # category, created = Category.objects.get_or_create(
                            #     name='Educativo',
                            #     defaults={'description': 'Recursos educativos'}
                            # )
                            
                            # multimedia = MultimediaCard.objects.create(
                            #     title=activity_title,
                            #     description=f'Recurso multimedia: {activity_title}',
                            #     media_type='document',
                            #     educational_level='primaria',
                            #     subject_area='General',
                            #     author=request.user
                            # )
                            
                            activities_created.append({
                                'type': 'multimedia',
                                'title': activity_title,
                                'id': 0  # Placeholder
                            })
                            
                        elif activity_type == 'guide':
                            # Crear guía pedagógica básica - omitir por ahora
                            # from apps.pedagogical_guides.models import Guide
                            
                            # guide = Guide.objects.create(
                            #     title=activity_title,
                            #     description=f'Guía pedagógica: {activity_title}',
                            #     author=request.user,
                            #     is_public=True
                            # )
                            
                            activities_created.append({
                                'type': 'guide',
                                'title': activity_title,
                                'id': 0  # Placeholder
                            })
                            
                except json.JSONDecodeError:
                    pass  # Ignorar errores de JSON
                except Exception as e:
                    # Log del error pero continuar con la creación de la clase
                    print(f"Error creando actividades iniciales: {e}")
            
            return JsonResponse({
                'success': True,
                'message': 'Clase creada exitosamente',
                'course_id': classroom.id,
                'activities_created': activities_created,
                'debug_info': {
                    'classroom_id': classroom.id,
                    'classroom_name': classroom.name,
                    'teacher_id': classroom.teacher.id,
                    'teacher_name': classroom.teacher.get_full_name()
                }
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
            classroom = Classroom.objects.get(code=code)
        except Classroom.DoesNotExist:
            return JsonResponse({'error': 'Código de clase inválido'}, status=404)
        
        # Verificar si ya está inscrito
        if ClassroomStudent.objects.filter(classroom=classroom, student=request.user).exists():
            return JsonResponse({'error': 'Ya estás inscrito en esta clase'}, status=400)
        
        # Inscribir al estudiante
        ClassroomStudent.objects.create(
            classroom=classroom,
            student=request.user,
            joined_at=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Te has unido a la clase exitosamente',
            'course_id': classroom.id,
            'redirect_url': f'/accounts/class/student/{classroom.id}/'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ============================================================================
# APIs DE MENSAJERÍA
# ============================================================================

@login_required
def get_message_api(request, message_id):
    """API para obtener detalles de un mensaje"""
    try:
        message = get_object_or_404(Message, id=message_id)
        
        # Verificar que el usuario tiene acceso al mensaje
        if message.sender != request.user and message.recipient != request.user:
            return JsonResponse({'error': 'No autorizado'}, status=403)
        
        # Marcar como leído si el usuario es el destinatario
        if message.recipient == request.user and not message.is_read:
            message.is_read = True
            message.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'subject': message.subject,
                'content': message.content,
                'sender_name': message.sender.get_full_name(),
                'sender_initials': f"{message.sender.first_name[0]}{message.sender.last_name[0]}".upper(),
                'created_at': message.created_at.strftime('%d/%m/%Y %H:%M'),
                'is_read': message.is_read
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_conversation_api(request, conversation_id):
    """API para obtener una conversación y sus mensajes"""
    try:
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        
        # Obtener el otro participante
        other_participant = conversation.participants.exclude(id=request.user.id).first()
        
        # Obtener mensajes de la conversación
        messages = conversation.conversation_messages.all().order_by('created_at')
        
        # Marcar mensajes como leídos
        conversation.mark_as_read_for_user(request.user)
        
        messages_data = []
        for msg in messages:
            messages_data.append({
                'id': msg.id,
                'content': msg.content,
                'is_sent': msg.sender == request.user,
                'created_at': msg.created_at.strftime('%d/%m/%Y %H:%M'),
                'sender_name': msg.sender.get_full_name()
            })
        
        return JsonResponse({
            'success': True,
            'conversation': {
                'id': conversation.id,
                'participant_name': other_participant.get_full_name() if other_participant else 'Usuario',
                'participant_initials': f"{other_participant.first_name[0]}{other_participant.last_name[0]}".upper() if other_participant else 'U',
            },
            'messages': messages_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def send_message_student_api(request):
    """API para que estudiantes envíen mensajes"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        
        content = data.get('content')
        message_id = data.get('message_id')
        conversation_id = data.get('conversation_id')
        
        if not content:
            return JsonResponse({'error': 'Contenido del mensaje requerido'}, status=400)
        
        if message_id:
            # Responder a un mensaje existente
            original_message = get_object_or_404(Message, id=message_id)
            
            # Verificar que el usuario tiene acceso al mensaje
            if original_message.sender != request.user and original_message.recipient != request.user:
                return JsonResponse({'error': 'No autorizado'}, status=403)
            
            # Crear respuesta
            recipient = original_message.sender if original_message.sender != request.user else original_message.recipient
            message = Message.objects.create(
                sender=request.user,
                recipient=recipient,
                subject=f"Re: {original_message.subject}",
                content=content,
                parent_message=original_message
            )
            
        elif conversation_id:
            # Enviar mensaje a una conversación
            conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
            
            # Crear mensaje en la conversación
            conversation_message = ConversationMessage.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            
        else:
            return JsonResponse({'error': 'Se requiere message_id o conversation_id'}, status=400)
        
        return JsonResponse({
            'success': True,
            'message': 'Mensaje enviado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def mark_message_read_api(request, message_id):
    """API para marcar un mensaje como leído"""
    try:
        message = get_object_or_404(Message, id=message_id, recipient=request.user)
        message.is_read = True
        message.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Mensaje marcado como leído'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== VISTAS AJAX PARA ACTUALIZACIÓN PARCIAL DE DASHBOARDS =====

from django.template.loader import render_to_string

@login_required
def teacher_courses_partial(request):
    """Vista AJAX para actualizar la lista de cursos del docente"""
    try:
        # Obtener cursos del docente
        courses = Classroom.objects.filter(teacher=request.user)
        course_stats = []
        
        for course in courses:
            # Contar estudiantes
            students_count = ClassroomStudent.objects.filter(classroom=course).count()
            
            # Obtener tareas pendientes (ejemplo)
            pending_submissions = 0  # Aquí iría la lógica real
            
            # Calcular promedio (ejemplo)
            avg_grade = 85  # Aquí iría la lógica real
            
            # Contar tareas
            assignments_count = Activities.objects.filter(IDaula=course).count()
            
            course_stats.append({
                'course': course,
                'students_count': students_count,
                'pending_submissions': pending_submissions,
                'avg_grade': avg_grade,
                'assignments_count': assignments_count,
            })
        
        html = render_to_string('dashboards/partials/teacher_courses_list.html', {
            'course_stats': course_stats
        }, request)
        
        return JsonResponse({'html': html})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def teacher_pending_submissions_partial(request):
    """Vista AJAX para actualizar las tareas pendientes de calificar"""
    try:
        # Obtener tareas pendientes del docente
        pending_submissions = []  # Aquí iría la lógica real para obtener submissions
        
        html = render_to_string('dashboards/partials/teacher_pending_submissions.html', {
            'pending_submissions': pending_submissions
        }, request)
        
        return JsonResponse({'html': html})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def student_courses_partial(request):
    """Vista AJAX para actualizar la lista de cursos del estudiante"""
    try:
        # Obtener cursos del estudiante
        student_enrollments = ClassroomStudent.objects.filter(student=request.user)
        course_details = []
        
        for enrollment in student_enrollments:
            course = enrollment.classroom
            # Calcular progreso (ejemplo)
            progress = 75  # Aquí iría la lógica real
            
            course_details.append({
                'id': course.id,
                'name': course.name,
                'teacher': course.teacher.get_full_name(),
                'progress': progress,
            })
        
        html = render_to_string('dashboards/partials/student_courses_list.html', {
            'course_details': course_details
        }, request)
        
        return JsonResponse({'html': html})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def student_achievements_partial(request):
    """Vista AJAX para actualizar los logros del estudiante"""
    try:
        # Obtener logros del estudiante
        recent_achievements = []  # Aquí iría la lógica real
        
        html = render_to_string('dashboards/partials/student_achievements_list.html', {
            'recent_achievements': recent_achievements
        }, request)
        
        return JsonResponse({'html': html})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def parent_children_partial(request):
    """Vista AJAX para actualizar la lista de hijos del padre"""
    try:
        # Obtener hijos del padre
        children = []  # Aquí iría la lógica real
        
        html = render_to_string('dashboards/partials/parent_children_list.html', {
            'children': children
        }, request)
        
        return JsonResponse({'html': html})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def admin_users_partial(request):
    """Vista AJAX para actualizar la lista de usuarios del admin"""
    try:
        # Obtener usuarios
        users = User.objects.all()[:10]  # Limitar a 10 usuarios
        
        html = render_to_string('dashboards/partials/admin_users_list.html', {
            'users': users
        }, request)
        
        return JsonResponse({'html': html})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== FUNCIONES DE ACTUALIZACIÓN AJAX GENÉRICAS =====

def reload_dashboard_section(section_name, user_type):
    """Función genérica para recargar secciones del dashboard"""
    endpoints = {
        'teacher_courses': 'ajax_teacher_courses',
        'teacher_pending': 'ajax_teacher_pending_submissions',
        'student_courses': 'ajax_student_courses',
        'student_achievements': 'ajax_student_achievements',
        'parent_children': 'ajax_parent_children',
        'admin_users': 'ajax_admin_users',
    }
    
    if section_name in endpoints:
        return f"reload{section_name.replace('_', '').title()}()"
    return None

# ===== VISTAS AJAX PARA ACTUALIZACIÓN PARCIAL =====

@login_required
def ajax_teacher_courses(request):
    """Vista AJAX para actualizar la sección de cursos del docente"""
    if request.user.user_type != 2:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        teacher_courses = Course.objects.filter(teacher=request.user)
        course_stats = []
        
        for course in teacher_courses[:4]:
            enrollments = Enrollment.objects.filter(course=course)
            students_count = enrollments.count()
            
            # Promedio general del curso
            submissions = AssignmentSubmission.objects.filter(
                assignment__course=course,
                grade__isnull=False
            )
            avg_grade = submissions.aggregate(avg=Avg('grade'))['avg'] or 0
            
            course_stats.append({
                'course': course,
                'students_count': students_count,
                'avg_grade': round(avg_grade, 1),
                'assignments_count': Assignment.objects.filter(course=course).count(),
                'pending_submissions': AssignmentSubmission.objects.filter(
                    assignment__course=course,
                    grade__isnull=True
                ).count()
            })
        
        html = render_to_string('partials/teacher_courses_section.html', {
            'course_stats': course_stats
        }, request=request)
        
        return JsonResponse({'html': html})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def ajax_teacher_pending_submissions(request):
    """Vista AJAX para actualizar la sección de tareas pendientes del docente"""
    if request.user.user_type != 2:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        pending_submissions = AssignmentSubmission.objects.filter(
            assignment__course__teacher=request.user,
            grade__isnull=True
        ).select_related('student', 'assignment', 'assignment__course').order_by('-submitted_at')[:5]
        
        html = render_to_string('partials/teacher_pending_section.html', {
            'pending_submissions': pending_submissions
        }, request=request)
        
        return JsonResponse({'html': html})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def ajax_student_courses(request):
    """Vista AJAX para actualizar la sección de cursos del estudiante"""
    try:
        enrollments = Enrollment.objects.filter(student=request.user).select_related('course', 'course__subject')
        course_details = []
        
        for enrollment in enrollments[:3]:
            try:
                course = enrollment.course
                teacher_name = "Sin asignar"
                try:
                    teacher_name = course.teacher.get_full_name() if course.teacher else "Sin asignar"
                except:
                    pass
                
                course_details.append({
                    'id': course.id,
                    'name': course.name,
                    'teacher': teacher_name,
                    'progress': enrollment.progress,
                })
            except Exception as e:
                print(f"Error procesando course details: {e}")
                continue
        
        html = render_to_string('partials/student_courses_section.html', {
            'course_details': course_details
        }, request=request)
        
        return JsonResponse({'html': html})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def ajax_student_achievements(request):
    """Vista AJAX para actualizar la sección de logros del estudiante"""
    try:
        recent_achievements = StudentAchievement.objects.filter(
            student=request.user
        ).select_related('achievement').order_by('-earned_at')[:6]
        
        html = render_to_string('partials/student_achievements_section.html', {
            'recent_achievements': recent_achievements
        }, request=request)
        
        return JsonResponse({'html': html})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def ajax_parent_children(request):
    """Vista AJAX para actualizar la sección de hijos del padre"""
    if request.user.user_type != 3:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        # Obtener hijos del padre (asumiendo que hay una relación)
        children = User.objects.filter(
            parent=request.user,
            user_type=1
        ).order_by('first_name', 'last_name')
        
        html = render_to_string('partials/parent_children_section.html', {
            'children': children
        }, request=request)
        
        return JsonResponse({'html': html})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def ajax_admin_users(request):
    """Vista AJAX para actualizar la sección de usuarios del admin"""
    if request.user.user_type != 4:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        users = User.objects.all().order_by('first_name', 'last_name')[:10]
        
        html = render_to_string('partials/admin_users_section.html', {
            'users': users
        }, request=request)
        
        return JsonResponse({'html': html})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== VISTAS DE MENSAJERÍA =====

@login_required
def messages_list(request):
    """Vista principal de mensajería para todos los usuarios"""
    user = request.user
    
    # Obtener conversaciones del usuario
    conversations = Conversation.objects.filter(participants=user).order_by('-updated_at')
    
    # Obtener mensajes directos
    direct_messages = Message.objects.filter(
        Q(sender=user) | Q(recipient=user)
    ).select_related('sender', 'recipient').order_by('-created_at')
    
    # Contar mensajes no leídos
    unread_count = Message.objects.filter(
        recipient=user,
        is_read=False
    ).count()
    
    # Obtener usuarios disponibles para mensajear según el tipo de usuario
    available_users = []
    if user.user_type == 2:  # Docente
        # Puede mensajear a sus estudiantes
        student_enrollments = Enrollment.objects.filter(
            course__teacher=user
        ).select_related('student')
        available_users = [enrollment.student for enrollment in student_enrollments]
    elif user.user_type == 1:  # Estudiante
        # Puede mensajear a sus docentes
        teacher_enrollments = Enrollment.objects.filter(
            student=user
        ).select_related('course__teacher')
        available_users = [enrollment.course.teacher for enrollment in teacher_enrollments if enrollment.course.teacher]
    elif user.user_type == 3:  # Padre
        # Puede mensajear a docentes de sus hijos
        children = User.objects.filter(parent=user, user_type=1)
        for child in children:
            child_enrollments = Enrollment.objects.filter(student=child).select_related('course__teacher')
            for enrollment in child_enrollments:
                if enrollment.course.teacher and enrollment.course.teacher not in available_users:
                    available_users.append(enrollment.course.teacher)
    
    context = {
        'user': user,
        'conversations': conversations,
        'direct_messages': direct_messages[:20],
        'unread_count': unread_count,
        'available_users': available_users,
    }
    
    return render(request, 'messages/messages_list.html', context)

@login_required
def conversation_detail(request, conversation_id):
    """Vista para mostrar una conversación específica"""
    try:
        conversation = Conversation.objects.get(id=conversation_id, participants=request.user)
    except Conversation.DoesNotExist:
        messages.error(request, 'Conversación no encontrada')
        return redirect('users:messages_list')
    
    if request.method == 'POST':
        message_content = request.POST.get('message')
        if message_content.strip():
            ConversationMessage.objects.create(
                conversation=conversation,
                sender=request.user,
                content=message_content
            )
            conversation.updated_at = timezone.now()
            conversation.save()
            return redirect('users:conversation_detail', conversation_id=conversation_id)
    
    # Marcar mensajes como leídos
    ConversationMessage.objects.filter(
        conversation=conversation,
        sender__in=conversation.participants.exclude(id=request.user.id),
        is_read=False
    ).update(is_read=True)
    
    context = {
        'conversation': conversation,
        'messages': conversation.conversation_messages.all().order_by('created_at'),
    }
    
    return render(request, 'messages/conversation_detail.html', context)

@login_required
def start_conversation(request, user_id):
    """Vista para iniciar una nueva conversación con un usuario"""
    try:
        other_user = User.objects.get(id=user_id)
        
        # Verificar permisos según el tipo de usuario
        can_message = False
        if request.user.user_type == 2:  # Docente
            can_message = Enrollment.objects.filter(
                student=other_user,
                course__teacher=request.user
            ).exists()
        elif request.user.user_type == 1:  # Estudiante
            can_message = Enrollment.objects.filter(
                student=request.user,
                course__teacher=other_user
            ).exists()
        elif request.user.user_type == 3:  # Padre
            children = User.objects.filter(parent=request.user, user_type=1)
            can_message = Enrollment.objects.filter(
                student__in=children,
                course__teacher=other_user
            ).exists()
        
        if not can_message:
            messages.error(request, 'No tienes permisos para mensajear con este usuario')
            return redirect('users:messages_list')
        
        # Crear o obtener conversación existente
        conversation, created = Conversation.objects.get_or_create(
            participants=request.user
        )
        conversation.participants.add(other_user)
        
        return redirect('users:conversation_detail', conversation_id=conversation.id)
        
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado')
        return redirect('users:messages_list')

# ===== VISTAS DE AULA VIRTUAL CON MENSAJERÍA =====

@login_required
def class_chat(request, class_id):
    """Vista para el chat de aula virtual"""
    try:
        classroom = get_object_or_404(Classroom, id=class_id)
        
        # Verificar permisos
        if request.user.user_type == 2:  # Docente
            if classroom.teacher != request.user:
                messages.error(request, 'No tienes permisos para acceder a esta clase')
                return redirect('users:dashboard_teacher', user_id=request.user.id)
        else:  # Estudiante
            if not ClassroomStudent.objects.filter(classroom=classroom, student=request.user).exists():
                messages.error(request, 'No estás inscrito en esta clase')
                return redirect('users:dashboard_student', user_id=request.user.id)
        
        # Obtener o crear conversación del aula
        conversation, created = Conversation.objects.get_or_create(
            id=classroom.id,
            defaults={'name': f'Chat de {classroom.name}'}
        )
        
        # Agregar participantes si es nueva
        if created:
            conversation.participants.add(request.user)
            if request.user.user_type == 2:  # Docente
                students = ClassroomStudent.objects.filter(classroom=classroom)
                for student_enrollment in students:
                    conversation.participants.add(student_enrollment.student)
            else:  # Estudiante
                conversation.participants.add(classroom.teacher)
        
        if request.method == 'POST':
            message_content = request.POST.get('message')
            if message_content.strip():
                ConversationMessage.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=message_content
                )
                conversation.updated_at = timezone.now()
                conversation.save()
                return redirect('users:class_chat', class_id=class_id)
        
        # Marcar mensajes como leídos
        ConversationMessage.objects.filter(
            conversation=conversation,
            sender__in=conversation.participants.exclude(id=request.user.id),
            is_read=False
        ).update(is_read=True)
        
        context = {
            'classroom': classroom,
            'conversation': conversation,
            'messages': conversation.conversation_messages.all().order_by('created_at'),
        }
        
        return render(request, 'class/class_chat.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al acceder al chat: {str(e)}')
        return redirect('users:dashboard_student', user_id=request.user.id)

# ===== GESTIÓN DE CURSOS =====

@login_required
def course_detail(request, course_id):
    """Vista detallada de un curso - redirige a la vista de clase correspondiente"""
    try:
        from apps.educational_games.gamification.models import Classroom, ClassroomStudent
        classroom = Classroom.objects.get(id=course_id)
        
        # Verificar si el usuario está inscrito
        is_enrolled = ClassroomStudent.objects.filter(
            student=request.user, 
            classroom=classroom
        ).exists()
        
        if request.user.user_type == 2:  # Docente
            if classroom.teacher == request.user:
                return redirect('users:class_teacher', class_id=course_id)
            else:
                messages.error(request, 'No tienes permisos para acceder a esta clase')
                return redirect('users:dashboard_teacher', user_id=request.user.id)
        else:  # Estudiante
            if is_enrolled:
                return redirect('users:class_student', class_id=course_id)
            else:
                messages.error(request, 'No estás inscrito en esta clase')
                return redirect('users:dashboard_student', user_id=request.user.id)
                
    except Classroom.DoesNotExist:
        messages.error(request, 'Curso no encontrado')
        return redirect('users:dashboard_student', user_id=request.user.id)

def generate_unique_class_code():
    """Genera un código único para el aula de 6 caracteres alfanuméricos"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Classroom.objects.filter(code=code).exists():
            return code

# ... existing code ...