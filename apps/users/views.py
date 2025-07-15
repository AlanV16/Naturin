from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages 
from django.contrib.auth import login, authenticate
from .models import User, Event, Message, Conversation, ConversationMessage, Child, Suggestion, EducationalResource
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
from django.views.decorators.http import require_http_methods, require_GET
from validate_email import validate_email
from django.core.paginator import Paginator
from django.contrib.auth import logout
import random
import string
from django.db import transaction
from apps.educational_games.gamification.models import ( Classroom, ClassroomStudent )
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
    """Dashboard específico para estudiantes"""
    # Comprobación de seguridad para evitar bucles y accesos incorrectos
    if request.user.id != user_id or request.user.user_type != 1:
        return redirect_to_user_dashboard(request)
    try:
        user = request.user
        
        # Verificar que el usuario es estudiante
        if user.user_type != 1:
            messages.error(request, 'Acceso denegado. Solo estudiantes pueden acceder a este dashboard.')
            return redirect('users:login')
        
        # Obtener las clases del estudiante usando el modelo correcto
        from apps.educational_games.gamification.models import ClassroomStudent, Classroom, Niveles
        inscripciones = ClassroomStudent.objects.filter(student=user).select_related('classroom', 'classroom__teacher')
        courses = []
        
        # Procesar inscripciones de forma segura
        for inscripcion in inscripciones:
            try:
                courses.append(inscripcion.classroom)
            except Exception as e:
                print(f"Error procesando inscripción: {e}")
                continue
        
        # Obtener información del nivel del estudiante
        try:
            nivel_info = Niveles.objects.get(IDusuario=user)
            student_level = nivel_info.nivel
            total_points = nivel_info.puntos_acumulados
        except Niveles.DoesNotExist:
            student_level = 1
            total_points = 0
        
        # Estadísticas básicas
        active_courses = len(courses)
        pending_assignments = 0  # Implementar cuando se tenga el sistema de tareas
        upcoming_events = 0  # Implementar cuando se tenga el sistema de eventos
        total_achievements = 0  # Implementar cuando se tenga el sistema de logros
        
        # Datos de rendimiento académico
        performance_data = {
            'completed': 75,  # Porcentaje de actividades completadas
            'pending': 25,    # Porcentaje de actividades pendientes
            'grade_letter': 'B+',
            'average_grade': 85.5,
            'ranking': 'N/A'
        }
        
        # Actividades recientes (temporalmente vacío)
        recent_activities = []
        
        # Logros recientes (temporalmente vacío)
        recent_achievements = []
        
        context = {
            'user': user,
            'course_details': courses,
            'active_courses': active_courses,
            'pending_assignments': pending_assignments,
            'upcoming_events': upcoming_events,
            'total_achievements': total_achievements,
            'performance_data': performance_data,
            'recent_activities': recent_activities,
            'recent_achievements': recent_achievements,
            'student_level': student_level,
            'total_points': total_points,
        }
        
        return render(request, 'dashboards/dashboard_student.html', context)
        
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('users:login')
    except Exception as e:
        messages.error(request, f'Error al cargar el dashboard: {str(e)}')
        return redirect('users:login')

@login_required
def dashboard_teacher(request, user_id):
    """Dashboard específico para docentes"""
    # Comprobación de seguridad para evitar bucles y accesos incorrectos
    if request.user.id != user_id or request.user.user_type != 2:
        return redirect_to_user_dashboard(request)
    try:
        user = request.user
        
        # Verificar que el usuario es docente
        if user.user_type != 2:
            messages.error(request, 'Acceso denegado. Solo docentes pueden acceder a este dashboard.')
            return redirect('users:login')
        
        # Obtener cursos del docente
        from apps.educational_games.gamification.models import Classroom, ClassroomStudent
        courses = Classroom.objects.filter(teacher=user)
        
        # Estadísticas
        course_stats = []
        total_students = 0
        pending_count = 0
        
        for course in courses:
            students_count = ClassroomStudent.objects.filter(classroom=course).count()
            total_students += students_count
            
            # Calcular estadísticas del curso
            avg_grade = 85.0  # Temporal
            assignments_count = 0  # Temporal
            
            course_stats.append({
                'classroom': course,
                'students_count': students_count,
                'avg_grade': avg_grade,
                'assignments_count': assignments_count,
                'status': 'active'
            })
        
        # Actividades recientes (temporal)
        recent_activities = []
        
        # Logros recientes (temporal)
        recent_achievements = []
        
        # Tareas pendientes de calificar (temporal)
        pending_submissions = []
        
        context = {
            'user': user,
            'course_stats': course_stats,
            'total_students': total_students,
            'pending_count': pending_count,
            'recent_activities': recent_activities,
            'recent_achievements': recent_achievements,
            'pending_submissions': pending_submissions,
            'active_courses': len(courses),
        }
        
        return render(request, 'dashboards/dashboard_teacher.html', context)
        
    except Exception as e:
        print(f"Error en dashboard_teacher: {e}")
        messages.error(request, 'Error al cargar el dashboard.')
        return redirect('users:login')

@login_required
def dashboard_parent(request, user_id):
    """Dashboard principal para padres"""
    try:
        user = User.objects.get(id=user_id, user_type=3)
        
        # Verificar que el usuario logueado sea el padre
        if request.user != user:
            return redirect('users:dashboard_parent', user_id=request.user.id)
        
        # Obtener datos para el dashboard
        children = user.children.all()
        children_count = children.count()
        
        # Obtener cursos de los hijos
        courses_count = 0
        overdue_assignments = 0
        upcoming_events = 0
        
        for child in children:
            # Contar cursos del hijo
            child_courses = Course.objects.filter(student=child).count()
            courses_count += child_courses
            
            # Contar tareas atrasadas
            child_assignments = Assignment.objects.filter(
                course__student=child,
                due_date__lt=timezone.now()
            ).count()
            overdue_assignments += child_assignments
            
            # Contar eventos próximos
            child_events = Event.objects.filter(
                student=child,
                start_date__gte=timezone.now()
            ).count()
            upcoming_events += child_events
        
        # Obtener actividades recientes
        recent_activities = []
        
        # Actividades de los hijos (últimas 5)
        for child in children:
            child_activities = {
                'description': f'{child.name} completó una actividad',
                'date': timezone.now().strftime('%d/%m/%Y'),
                'time': timezone.now(),
                'type': 'activity'
            }
            recent_activities.append(child_activities)
        
        # Eventos próximos para mostrar en la lista
        upcoming_events_list = []
        for child in children:
            child_events = Event.objects.filter(
                student=child,
                start_date__gte=timezone.now()
            ).order_by('start_date')[:3]
            
            for event in child_events:
                upcoming_events_list.append({
                    'title': event.title,
                    'day': event.start_date.strftime('%d'),
                    'month': event.start_date.strftime('%b'),
                    'time': event.start_date.strftime('%H:%M'),
                    'location': event.location or 'Sin ubicación',
                    'student': child.name
                })
        
        context = {
            'user': user,
            'children': children,
            'children_count': children_count,
            'courses_count': courses_count,
            'overdue_assignments': overdue_assignments,
            'upcoming_events': upcoming_events,
            'recent_activities': recent_activities[:5],
            'upcoming_events_list': upcoming_events_list[:5],
        }
        
        return render(request, 'dashboards/dashboard_parent.html', context)
        
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado')
        return redirect('users:login')
    except Exception as e:
        messages.error(request, 'Error al cargar el dashboard')
        return redirect('users:login')

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
    from apps.educational_games.gamification.models import Classroom
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
    """Vista para que estudiantes se unan a una clase"""
    if request.method == 'POST':
        # Aceptar tanto 'class_code' como 'course_code' para compatibilidad
        class_code = request.POST.get('class_code') or request.POST.get('course_code')
        
        if not class_code:
            messages.error(request, 'Por favor ingresa el código de la clase.')
            return redirect('users:dashboard_student', user_id=request.user.id)
        
        try:
            # Buscar la clase solo por código
            from apps.educational_games.gamification.models import Classroom, ClassroomStudent
            classroom = Classroom.objects.get(code=class_code)
            
            # Verificar si el estudiante ya está en la clase
            if ClassroomStudent.objects.filter(classroom=classroom, student=request.user).exists():
                messages.warning(request, 'Ya estás inscrito en esta clase.')
                return redirect('users:dashboard_student', user_id=request.user.id)
            
            # Inscribir al estudiante
            ClassroomStudent.objects.create(
                classroom=classroom,
                student=request.user
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
    """Vista para que docentes creen una nueva clase"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'No tienes permisos para crear clases.')
        return redirect('users:dashboard_teacher')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Generar código único automáticamente
                from .utils import generate_unique_class_code
                code = generate_unique_class_code()
                
                # Validar campos requeridos
                required_fields = ['class_name', 'grade', 'section']
                for field in required_fields:
                    if not request.POST.get(field):
                        messages.error(request, f'El campo {field} es requerido.')
                        return redirect('users:create_class')
                
                # Crear la clase
                from apps.educational_games.gamification.models import Classroom
                classroom = Classroom.objects.create(
                    name=request.POST.get('class_name'),
                    description=request.POST.get('description', ''),
                    grade=request.POST.get('grade'),
                    section=request.POST.get('section'),
                    code=code,
                    teacher=request.user,
                    created_at=timezone.now()
                )
                
                messages.success(request, f'Clase "{classroom.name}" creada exitosamente. Código de clase: {code}')
                return redirect('users:class_teacher', class_id=classroom.id)
                
        except Exception as e:
            messages.error(request, f'Error al crear la clase: {str(e)}')
    
    context = {
        'grades': ['Primero', 'Segundo'],
        'sections': ['A', 'B', 'C', 'D', 'E'],
    }
    
    return render(request, 'class/create_class.html', context)

@login_required
def class_student(request, class_id):
    from apps.educational_games.gamification.models import Classroom, ClassroomStudent, Niveles
    classroom = get_object_or_404(Classroom, id=class_id)
    if not ClassroomStudent.objects.filter(classroom=classroom, student=request.user).exists():
        messages.error(request, 'No tienes acceso a esta clase.')
        return redirect('users:dashboard_student', user_id=request.user.id)
    
    # Obtener actividades (temporalmente vacío hasta implementar)
    activities = []
    try:
        progress = Niveles.objects.get(IDusuario=request.user)
    except Niveles.DoesNotExist:
        progress = None
    
    chat_messages = []
    context = {
        'classroom': classroom,
        'activities': activities,
        'progress': progress,
        'chat_messages': chat_messages,
    }
    
    return render(request, 'class/class_student.html', context)

@login_required
def class_teacher(request, class_id):
    """Vista de clase para docentes con funcionalidades integradas de gamificación"""
    try:
        from apps.educational_games.gamification.models import Classroom, ClassroomStudent
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
    
    # Obtener estudiantes inscritos
    students = ClassroomStudent.objects.filter(classroom=classroom).select_related('student')
    
    # Obtener actividades específicas de la clase (temporalmente vacío)
    activities = []
    
    context = {
        'classroom': classroom,
        'students': students,
        'activities': activities,
        'user': request.user,
    }
    
    return render(request, 'class/class_teacher.html', context)

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
        code = generate_unique_class_code()
        return JsonResponse({'code': code})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def create_class_api(request):
    """API para crear una nueva clase"""
    if request.user.user_type != 2:  # Solo docentes
        return JsonResponse({'success': False, 'error': 'No tienes permisos para crear clases.'})
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Generar código único
                from .utils import generate_unique_class_code
                code = None
                try:
                    code = generate_unique_class_code()
                except Exception as e:
                    import logging
                    logging.error(f"Error generando código de clase: {e}")
                    return JsonResponse({'success': False, 'error': f'Error generando el código de la clase: {str(e)}'})
                if not code:
                    return JsonResponse({'success': False, 'error': 'No se pudo generar un código de clase único.'})
                
                # Validar campos requeridos
                required_fields = ['class_name', 'grade', 'section']
                for field in required_fields:
                    if not request.POST.get(field):
                        return JsonResponse({'success': False, 'error': f'El campo {field} es requerido.'})
                
                # Crear la clase
                from apps.educational_games.gamification.models import Classroom
                classroom = Classroom.objects.create(
                    name=request.POST.get('class_name'),
                    description=request.POST.get('description', ''),
                    grade=request.POST.get('grade'),
                    section=request.POST.get('section'),
                    code=code,
                    teacher=request.user,
                    created_at=timezone.now()
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'Clase "{classroom.name}" creada exitosamente.',
                    'course_id': classroom.id,
                    'code': code,
                    'redirect_url': reverse('users:class_teacher', args=[classroom.id])
                })
        except Exception as e:
            import logging
            logging.error(f"Error al crear la clase: {e}")
            return JsonResponse({'success': False, 'error': f'Error al crear la clase: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido.'})

@login_required
def join_class_api(request):
    """API para que estudiantes se unan a una clase"""
    if request.method == 'POST':
        class_code = request.POST.get('code')
        
        if not class_code:
            return JsonResponse({'success': False, 'error': 'Por favor ingresa el código de la clase.'})
        
        try:
            from apps.educational_games.gamification.models import Classroom, ClassroomStudent
            classroom = Classroom.objects.get(code=class_code)
            
            # Verificar si el estudiante ya está en la clase
            if ClassroomStudent.objects.filter(classroom=classroom, student=request.user).exists():
                return JsonResponse({'success': False, 'error': 'Ya estás inscrito en esta clase.'})
            
            # Inscribir al estudiante
            ClassroomStudent.objects.create(
                classroom=classroom,
                student=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Te has unido exitosamente a la clase "{classroom.name}"',
                'redirect_url': reverse('users:class_student', args=[classroom.id])
            })
            
        except Classroom.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'No se encontró la clase con el código proporcionado.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al unirse a la clase: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido.'})

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
        courses = Aulas.objects.filter(IDdocente=request.user)
        course_stats = []
        
        for course in courses:
            # Contar estudiantes
            students_count = AulaEstudiante.objects.filter(IDaula=course).count()
            
            # Obtener tareas pendientes (ejemplo)
            pending_submissions = 0  # Aquí iría la lógica real
            
            # Calcular promedio (ejemplo)
            avg_grade = 85  # Aquí iría la lógica real
            
            # Contar tareas
            assignments_count = Actividades.objects.filter(IDaula=course).count()
            
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
        student_enrollments = AulaEstudiante.objects.filter(IDestudiante=request.user)
        course_details = []
        
        for enrollment in student_enrollments:
            course = enrollment.IDaula
            # Calcular progreso (ejemplo)
            progress = 75  # Aquí iría la lógica real
            
            course_details.append({
                'id': course.IDaula,
                'name': course.NombreAula,
                'teacher': course.IDdocente.get_full_name(),
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
    """Vista de chat para aulas virtuales"""
    try:
        from apps.educational_games.gamification.models import Classroom, ClassroomStudent, ClassroomMessage
        classroom = get_object_or_404(Classroom, id=class_id)
        
        # Verificar acceso
        if request.user.user_type == 2:  # Docente
            if classroom.teacher != request.user:
                messages.error(request, 'No tienes permisos para acceder a esta clase.')
                return redirect('users:dashboard_teacher', user_id=request.user.id)
        else:  # Estudiante
            if not ClassroomStudent.objects.filter(classroom=classroom, student=request.user).exists():
                messages.error(request, 'No tienes acceso a esta clase.')
                return redirect('users:dashboard_student', user_id=request.user.id)
        
        # Obtener mensajes del chat
        messages_list = ClassroomMessage.objects.filter(classroom=classroom).select_related('sender').order_by('created_at')
        
        context = {
            'classroom': classroom,
            'messages': messages_list,
            'user': request.user,
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
    from apps.educational_games.gamification.models import Classroom
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Classroom.objects.filter(code=code).exists():
            return code

# ============================================================================
# VISTAS FALTANTES - TEMPORALES PARA EVITAR ERRORES
# ============================================================================

@login_required
def teacher_tests(request):
    """Vista temporal para tests de docente"""
    return render(request, 'teachers/tests.html', {
        'user': request.user,
        'message': 'Función en desarrollo'
    })

@login_required
def teacher_readings(request):
    """Vista temporal para lecturas de docente"""
    return render(request, 'teachers/readings.html', {
        'user': request.user,
        'message': 'Función en desarrollo'
    })

@login_required
def teacher_games(request):
    """Vista temporal para juegos de docente"""
    return render(request, 'teachers/games.html', {
        'user': request.user,
        'message': 'Función en desarrollo'
    })

@login_required
def teacher_tests_enhanced(request):
    """Vista temporal para tests mejorados de docente"""
    return render(request, 'teachers/tests_enhanced.html', {
        'user': request.user,
        'message': 'Función en desarrollo'
    })

@login_required
def teacher_readings_enhanced(request):
    """Vista temporal para lecturas mejoradas de docente"""
    return render(request, 'teachers/readings_enhanced.html', {
        'user': request.user,
        'message': 'Función en desarrollo'
    })

@login_required
def teacher_games_enhanced(request):
    """Vista temporal para juegos mejorados de docente"""
    return render(request, 'teachers/games_enhanced.html', {
        'user': request.user,
        'message': 'Función en desarrollo'
    })

@login_required
@require_http_methods(["POST"])
def create_test_api(request):
    """API temporal para crear tests"""
    return JsonResponse({'success': False, 'message': 'Función en desarrollo'})

@login_required
@require_http_methods(["POST"])
def assign_reading_api(request):
    """API temporal para asignar lecturas"""
    return JsonResponse({'success': False, 'message': 'Función en desarrollo'})

@login_required
@require_http_methods(["POST"])
def assign_game_api(request):
    """API temporal para asignar juegos"""
    return JsonResponse({'success': False, 'message': 'Función en desarrollo'})

@login_required
def notifications_realtime_api(request):
    """API temporal para notificaciones en tiempo real"""
    return JsonResponse({'notifications': []})

@login_required
@require_http_methods(["POST"])
def create_notification_api(request):
    """API temporal para crear notificaciones"""
    return JsonResponse({'success': False, 'message': 'Función en desarrollo'})

@login_required
@require_http_methods(["POST"])
def mark_notification_read_realtime(request, notification_id):
    """API temporal para marcar notificación como leída"""
    return JsonResponse({'success': False, 'message': 'Función en desarrollo'})

@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read_realtime(request):
    """API temporal para marcar todas las notificaciones como leídas"""
    return JsonResponse({'success': False, 'message': 'Función en desarrollo'})

@login_required
@require_http_methods(["POST"])
def send_classroom_notification(request, class_id):
    """API temporal para enviar notificación de aula"""
    return JsonResponse({'success': False, 'message': 'Función en desarrollo'})

@login_required
def notification_settings(request):
    """Vista temporal para configuración de notificaciones"""
    return render(request, 'users/notification_settings.html', {
        'user': request.user,
        'message': 'Función en desarrollo'
    })

@login_required
def class_chat_api(request, class_id):
    """API para chat de aula"""
    try:
        classroom = get_object_or_404(Classroom, id=class_id)
        
        if request.method == 'POST':
            content = request.POST.get('message', '').strip()
            if content:
                # Crear mensaje usando el modelo correcto
                from apps.educational_games.gamification.models import ClassroomMessage
                message = ClassroomMessage.objects.create(
                    classroom=classroom,
                    sender=request.user,
                    content=content
                )
                return JsonResponse({
                    'success': True,
                    'message': {
                        'id': message.id,
                        'content': message.content,
                        'sender_name': message.sender.get_full_name(),
                        'created_at': message.created_at.isoformat()
                    }
                })
        
        # GET: Obtener mensajes
        from apps.educational_games.gamification.models import ClassroomMessage
        messages = ClassroomMessage.objects.filter(classroom=classroom).select_related('sender').order_by('created_at')
        
        messages_data = []
        for msg in messages:
            messages_data.append({
                'id': msg.id,
                'content': msg.content,
                'sender_id': msg.sender.id,
                'sender_name': msg.sender.get_full_name(),
                'is_own': msg.sender == request.user,
                'created_at': msg.created_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'messages': messages_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_http_methods(["POST"])
def create_activity_api(request):
    """API temporal para crear actividades"""
    return JsonResponse({'success': False, 'message': 'Función en desarrollo'})

@login_required
def password_reset_request(request):
    """Vista para solicitar restablecimiento de contraseña"""
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                # Generar código de restablecimiento
                reset_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                user.password_reset_code = reset_code
                user.password_reset_expires = timezone.now() + timedelta(hours=1)
                user.save()
                
                # Enviar email (implementación temporal)
                messages.success(request, f'Se ha enviado un código de restablecimiento a {email}')
                return redirect('users:password_reset_verify', user_id=user.id)
            except User.DoesNotExist:
                messages.error(request, 'No se encontró un usuario con ese email.')
        else:
            messages.error(request, 'Por favor ingresa tu email.')
    
    return render(request, 'accounts/password_reset_request.html')

# --- Recuperación de contraseña ---
@csrf_exempt
def password_reset_request(request):
    return render(request, 'accounts/password_reset_request.html')

@csrf_exempt
def password_reset_verify(request, user_id):
    return render(request, 'accounts/password_reset_verify.html', {'user_id': user_id})

@csrf_exempt
def password_reset_form(request, user_id, code):
    return render(request, 'accounts/password_reset_form.html', {'user_id': user_id, 'code': code})

@csrf_exempt
def password_reset_complete(request):
    return render(request, 'accounts/password_reset_complete.html')

@csrf_exempt
def resend_password_reset_code(request, user_id):
    return render(request, 'accounts/password_reset_request.html', {'resent': True, 'user_id': user_id})

@login_required
def add_child_ajax(request):
    """Vista AJAX para añadir hijo al dashboard de padres"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    if request.user.user_type != 3:  # Solo padres
        return JsonResponse({'success': False, 'error': 'Acceso no autorizado'})
    
    try:
        # Validar que no tenga más de 5 hijos
        parent_profile = getattr(request.user, 'parentprofile', None)
        if parent_profile and parent_profile.children.count() >= 5:
            return JsonResponse({
                'success': False, 
                'error': 'Ya tienes el máximo de 5 hijos registrados'
            })
        
        # Obtener datos del formulario
        child_name = request.POST.get('child_name', '').strip()
        child_grade = request.POST.get('child_grade')
        child_birthdate = request.POST.get('child_birthdate')
        child_document = request.POST.get('child_document', '').strip()
        
        # Validaciones
        if not child_name:
            return JsonResponse({'success': False, 'error': 'El nombre es obligatorio'})
        
        if not child_grade:
            return JsonResponse({'success': False, 'error': 'El grado es obligatorio'})
        
        if not child_birthdate:
            return JsonResponse({'success': False, 'error': 'La fecha de nacimiento es obligatoria'})
        
        # Validar fecha de nacimiento (debe ser menor de 18 años)
        from datetime import datetime, date
        birth_date = datetime.strptime(child_birthdate, '%Y-%m-%d').date()
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        
        if age >= 18:
            return JsonResponse({'success': False, 'error': 'El hijo debe ser menor de 18 años'})
        
        # Crear o obtener el perfil de padre
        parent_profile, created = ParentProfile.objects.get_or_create(user=request.user)
        
        # Crear el hijo (usuario tipo estudiante)
        from django.contrib.auth.models import User
        child_username = f"{request.user.username}_child_{parent_profile.children.count() + 1}"
        
        # Crear usuario para el hijo
        child_user = User.objects.create_user(
            username=child_username,
            email=f"{child_username}@naturein.local",
            first_name=child_name.split()[0] if ' ' in child_name else child_name,
            last_name=child_name.split()[-1] if ' ' in child_name else '',
            is_active=True
        )
        
        # Asignar tipo de usuario (estudiante = 1)
        child_user.user_type = 1
        child_user.save()
        
        # Crear perfil de estudiante para el hijo
        from apps.users.models import StudentProfile
        student_profile = StudentProfile.objects.create(
            user=child_user,
            grade=child_grade,
            birth_date=birth_date,
            document_number=child_document if child_document else None
        )
        
        # Agregar hijo al perfil de padre
        parent_profile.children.add(child_user)
        
        return JsonResponse({
            'success': True,
            'message': f'Hijo "{child_name}" añadido correctamente',
            'child_data': {
                'id': child_user.id,
                'name': child_name,
                'grade': child_grade,
                'progress': 0  # Progreso inicial
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'Error al añadir hijo: {str(e)}'
        })

# ============================================================================
# VISTAS AJAX PARA DASHBOARD DE PADRES
# ============================================================================

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.db.models import Q
import json

@login_required
@require_GET
def ajax_children_list(request):
    """Obtener lista de hijos del padre"""
    try:
        children = request.user.children.all()
        html = render_to_string('dashboards/partials/children_list.html', {
            'children': children,
            'request': request
        })
        return JsonResponse({
            'success': True,
            'html': html,
            'count': children.count()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al cargar la lista de hijos'
        })

@login_required
@require_POST
def ajax_add_child(request):
    """Añadir hijo via AJAX"""
    try:
        child_name = request.POST.get('child_name')
        child_grade = request.POST.get('child_grade')
        child_birthdate = request.POST.get('child_birthdate')
        child_document = request.POST.get('child_document', '')
        
        if not all([child_name, child_grade, child_birthdate]):
            return JsonResponse({
                'success': False,
                'error': 'Todos los campos obligatorios deben estar completos'
            })
        
        # Crear el hijo (asumiendo que tienes un modelo Child)
        child = Child.objects.create(
            parent=request.user,
            name=child_name,
            grade=child_grade,
            birthdate=child_birthdate,
            document=child_document
        )
        
        # Generar HTML para la nueva tarjeta de hijo
        html = render_to_string('dashboards/partials/child_card.html', {
            'child': child,
            'request': request
        })
        
        return JsonResponse({
            'success': True,
            'message': 'Hijo añadido correctamente',
            'html': html,
            'child_data': {
                'name': child.name,
                'grade': child.grade,
                'progress': getattr(child, 'progress', 0)
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al añadir hijo'
        })

@login_required
@require_POST
def ajax_delete_child(request):
    """Eliminar hijo via AJAX"""
    try:
        child_id = request.POST.get('child_id')
        child = Child.objects.get(id=child_id, parent=request.user)
        child.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Hijo eliminado correctamente'
        })
    except Child.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Hijo no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al eliminar hijo'
        })

@login_required
@require_GET
def ajax_chat_contacts(request):
    """Obtener contactos (docentes) para el chat"""
    try:
        # Obtener docentes de los cursos de los hijos
        children = request.user.children.all()
        teachers = []
        
        for child in children:
            # Asumiendo que tienes un modelo Course con relación a Teacher
            courses = Course.objects.filter(student=child)
            for course in courses:
                if course.teacher not in teachers:
                    teachers.append(course.teacher)
        
        # También incluir docentes con los que ya ha tenido conversaciones
        existing_contacts = Message.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user)
        ).values_list('sender', 'recipient').distinct()
        
        for sender_id, recipient_id in existing_contacts:
            if sender_id != request.user.id:
                teacher = User.objects.filter(id=sender_id, user_type=2).first()
                if teacher and teacher not in teachers:
                    teachers.append(teacher)
            if recipient_id != request.user.id:
                teacher = User.objects.filter(id=recipient_id, user_type=2).first()
                if teacher and teacher not in teachers:
                    teachers.append(teacher)
        
        html = render_to_string('dashboards/partials/chat_contacts.html', {
            'teachers': teachers,
            'request': request
        })
        
        return JsonResponse({
            'success': True,
            'html': html
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al cargar contactos'
        })

@login_required
@require_GET
def ajax_chat_messages(request, contact_id):
    """Obtener mensajes de un chat específico"""
    try:
        # Obtener mensajes entre el padre y el docente
        messages = Message.objects.filter(
            (Q(sender=request.user) & Q(recipient_id=contact_id)) |
            (Q(sender_id=contact_id) & Q(recipient=request.user))
        ).order_by('created_at')
        
        html = render_to_string('dashboards/partials/chat_messages.html', {
            'messages': messages,
            'user': request.user,
            'request': request
        })
        
        return JsonResponse({
            'success': True,
            'html': html
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al cargar mensajes'
        })

@login_required
@require_POST
def ajax_send_message(request):
    """Enviar mensaje via AJAX"""
    try:
        data = json.loads(request.body)
        contact_id = data.get('contact_id')
        text = data.get('text')
        
        if not all([contact_id, text]):
            return JsonResponse({
                'success': False,
                'error': 'Datos incompletos'
            })
        
        # Crear el mensaje usando el modelo existente
        message = Message.objects.create(
            sender=request.user,
            recipient_id=contact_id,
            content=text
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Mensaje enviado correctamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al enviar mensaje'
        })

@login_required
@require_GET
def ajax_upcoming_events(request):
    """Obtener eventos próximos de los hijos"""
    try:
        # Obtener eventos de los hijos del padre
        children = request.user.children.all()
        events = Event.objects.filter(
            student__in=children,
            date__gte=timezone.now().date()
        ).order_by('date')[:10]
        
        html = render_to_string('dashboards/partials/events_list.html', {
            'events': events,
            'request': request
        })
        
        return JsonResponse({
            'success': True,
            'html': html
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al cargar eventos'
        })

@login_required
@require_POST
def ajax_send_suggestion(request):
    """Enviar sugerencia via AJAX"""
    try:
        suggestion_type = request.POST.get('type')
        description = request.POST.get('description')
        
        if not all([suggestion_type, description]):
            return JsonResponse({
                'success': False,
                'error': 'Todos los campos son obligatorios'
            })
        
        # Crear la sugerencia
        suggestion = Suggestion.objects.create(
            parent=request.user,
            type=suggestion_type,
            description=description,
            created_at=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Sugerencia enviada correctamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al enviar sugerencia'
        })

@login_required
@require_GET
def ajax_suggestions_list(request):
    """Obtener lista de sugerencias enviadas"""
    try:
        suggestions = Suggestion.objects.filter(
            parent=request.user
        ).order_by('-created_at')
        
        html = render_to_string('dashboards/partials/suggestions_list.html', {
            'suggestions': suggestions,
            'request': request
        })
        
        return JsonResponse({
            'success': True,
            'html': html
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al cargar sugerencias'
        })

@login_required
@require_GET
def ajax_educational_resources(request):
    """Obtener recursos educativos para los hijos"""
    try:
        # Obtener grados de los hijos
        children_grades = request.user.children.values_list('grade', flat=True)
        
        # Obtener recursos para esos grados
        resources = EducationalResource.objects.filter(
            grade__in=children_grades
        ).order_by('title')
        
        html = render_to_string('dashboards/partials/resources_list.html', {
            'resources': resources,
            'request': request
        })
        
        return JsonResponse({
            'success': True,
            'html': html
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al cargar recursos educativos'
        })

@login_required
@require_GET
def ajax_search_teachers(request):
    """Buscar docentes por nombre o correo electrónico"""
    try:
        query = request.GET.get('q', '').strip()
        
        if len(query) < 2:
            return JsonResponse({
                'success': True,
                'teachers': [],
                'message': 'Ingresa al menos 2 caracteres para buscar'
            })
        
        # Buscar docentes por nombre o correo
        teachers = User.objects.filter(
            user_type=2,  # Docentes
            is_active=True
        ).filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(username__icontains=query)
        )[:10]  # Limitar a 10 resultados
        
        teachers_data = []
        for teacher in teachers:
            teachers_data.append({
                'id': teacher.id,
                'name': teacher.get_full_name(),
                'email': teacher.email,
                'avatar_url': teacher.avatar.url if teacher.avatar else None,
                'courses_count': teacher.taught_courses.count()
            })
        
        return JsonResponse({
            'success': True,
            'teachers': teachers_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al buscar docentes'
        })

@login_required
@require_GET
def ajax_teacher_info(request, teacher_id):
    """Obtener información de un docente específico"""
    try:
        teacher = User.objects.get(id=teacher_id, user_type=2, is_active=True)
        
        return JsonResponse({
            'success': True,
            'teacher': {
                'id': teacher.id,
                'name': teacher.get_full_name(),
                'email': teacher.email,
                'avatar_url': teacher.avatar.url if teacher.avatar else None,
                'courses_count': teacher.taught_courses.count()
            }
        })
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Docente no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al obtener información del docente'
        })

@login_required
@require_POST
def ajax_mark_messages_read(request, contact_id):
    """Marcar mensajes como leídos"""
    try:
        # Marcar mensajes recibidos como leídos
        Message.objects.filter(
            sender_id=contact_id,
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
        
        return JsonResponse({
            'success': True,
            'message': 'Mensajes marcados como leídos'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al marcar mensajes como leídos'
        })

@login_required
@require_GET
def ajax_unread_messages_count(request):
    """Obtener contador de mensajes no leídos"""
    try:
        count = Message.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        
        return JsonResponse({
            'success': True,
            'count': count
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al obtener contador de mensajes'
        })

@login_required
@require_GET
def ajax_dashboard_stats(request):
    """Obtener estadísticas actualizadas del dashboard"""
    try:
        user = request.user
        children = user.children.all()
        
        # Calcular estadísticas
        children_count = children.count()
        courses_count = 0
        overdue_assignments = 0
        upcoming_events = 0
        
        for child in children:
            # Contar cursos del hijo
            child_courses = Course.objects.filter(student=child).count()
            courses_count += child_courses
            
            # Contar tareas atrasadas
            child_assignments = Assignment.objects.filter(
                course__student=child,
                due_date__lt=timezone.now()
            ).count()
            overdue_assignments += child_assignments
            
            # Contar eventos próximos
            child_events = Event.objects.filter(
                student=child,
                start_date__gte=timezone.now()
            ).count()
            upcoming_events += child_events
        
        return JsonResponse({
            'success': True,
            'stats': {
                'children_count': children_count,
                'courses_count': courses_count,
                'overdue_assignments': overdue_assignments,
                'upcoming_events': upcoming_events
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al obtener estadísticas'
        })

@login_required
@require_GET
def ajax_recent_activities(request):
    """Obtener actividades recientes de los hijos"""
    try:
        user = request.user
        children = user.children.all()
        activities = []
        
        # Obtener actividades de los últimos 7 días
        for child in children:
            # Actividades de cursos
            child_courses = Course.objects.filter(student=child)
            for course in child_courses:
                # Simular actividades (en un sistema real, tendrías un modelo de actividades)
                activity = {
                    'description': f'{child.name} completó una tarea en {course.name}',
                    'date': timezone.now().strftime('%d/%m/%Y'),
                    'time': timezone.now(),
                    'type': 'assignment',
                    'child_name': child.name,
                    'course_name': course.name
                }
                activities.append(activity)
        
        # Ordenar por fecha (más recientes primero)
        activities.sort(key=lambda x: x['time'], reverse=True)
        
        html = render_to_string('dashboards/partials/recent_activities.html', {
            'activities': activities[:10],
            'request': request
        })
        
        return JsonResponse({
            'success': True,
            'html': html
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al cargar actividades'
        })

@login_required
@require_GET
def ajax_child_progress(request, child_id):
    """Obtener progreso detallado de un hijo"""
    try:
        child = Child.objects.get(id=child_id, parent=request.user)
        
        # Obtener cursos del hijo
        courses = Course.objects.filter(student=child)
        course_progress = []
        
        for course in courses:
            # Calcular progreso del curso (simulado)
            progress = min(100, max(0, random.randint(20, 95)))
            course_progress.append({
                'course_name': course.name,
                'progress': progress,
                'teacher': course.teacher.get_full_name(),
                'assignments_count': course.assignments.count(),
                'completed_assignments': course.assignments.filter(due_date__lt=timezone.now()).count()
            })
        
        return JsonResponse({
            'success': True,
            'child': {
                'name': child.name,
                'grade': child.grade,
                'overall_progress': sum(cp['progress'] for cp in course_progress) // len(course_progress) if course_progress else 0,
                'courses': course_progress
            }
        })
    except Child.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Hijo no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al obtener progreso'
        })

@login_required
@require_GET
def ajax_child_assignments(request, child_id):
    """Obtener tareas de un hijo"""
    try:
        child = Child.objects.get(id=child_id, parent=request.user)
        
        # Obtener tareas de los cursos del hijo
        assignments = Assignment.objects.filter(
            course__student=child
        ).order_by('due_date')
        
        assignments_data = []
        for assignment in assignments:
            # Verificar si está entregada
            submission = AssignmentSubmission.objects.filter(
                assignment=assignment,
                student=child
            ).first()
            
            assignments_data.append({
                'id': assignment.id,
                'title': assignment.title,
                'course': assignment.course.name,
                'due_date': assignment.due_date.strftime('%d/%m/%Y %H:%M'),
                'is_overdue': assignment.due_date < timezone.now(),
                'is_submitted': submission is not None,
                'grade': submission.grade if submission else None,
                'points': assignment.points
            })
        
        html = render_to_string('dashboards/partials/child_assignments.html', {
            'assignments': assignments_data,
            'child': child,
            'request': request
        })
        
        return JsonResponse({
            'success': True,
            'html': html
        })
    except Child.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Hijo no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al obtener tareas'
        })

@login_required
@require_GET
def ajax_child_grades(request, child_id):
    """Obtener calificaciones de un hijo"""
    try:
        child = Child.objects.get(id=child_id, parent=request.user)
        
        # Obtener calificaciones de las entregas
        submissions = AssignmentSubmission.objects.filter(
            student=child,
            grade__isnull=False
        ).order_by('-submitted_at')
        
        grades_data = []
        for submission in submissions:
            grades_data.append({
                'assignment': submission.assignment.title,
                'course': submission.assignment.course.name,
                'grade': submission.grade,
                'max_points': submission.assignment.points,
                'percentage': round((submission.grade / submission.assignment.points) * 100, 1),
                'submitted_date': submission.submitted_at.strftime('%d/%m/%Y'),
                'teacher': submission.assignment.course.teacher.get_full_name()
            })
        
        html = render_to_string('dashboards/partials/child_grades.html', {
            'grades': grades_data,
            'child': child,
            'request': request
        })
        
        return JsonResponse({
            'success': True,
            'html': html
        })
    except Child.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Hijo no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al obtener calificaciones'
        })

@login_required
@require_GET
def ajax_calendar_events(request):
    """Obtener eventos del calendario para los hijos"""
    try:
        user = request.user
        children = user.children.all()
        events = []
        
        for child in children:
            child_events = Event.objects.filter(
                student=child,
                start_date__gte=timezone.now()
            ).order_by('start_date')[:10]
            
            for event in child_events:
                events.append({
                    'id': event.id,
                    'title': event.title,
                    'start_date': event.start_date.isoformat(),
                    'end_date': event.end_date.isoformat(),
                    'student_name': child.name,
                    'course_name': event.course.name,
                    'location': event.location,
                    'event_type': event.event_type
                })
        
        return JsonResponse({
            'success': True,
            'events': events
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al cargar eventos del calendario'
        })

@login_required
@require_GET
def ajax_notifications(request):
    """Obtener notificaciones del padre"""
    try:
        notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:20]
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.type,
                'is_read': notification.is_read,
                'created_at': notification.created_at.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'notifications': notifications_data,
            'count': notifications.count()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al cargar notificaciones'
        })

@login_required
@require_POST
def ajax_mark_all_notifications_read(request):
    """Marcar todas las notificaciones como leídas"""
    try:
        Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)
        
        return JsonResponse({
            'success': True,
            'message': 'Todas las notificaciones marcadas como leídas'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al marcar notificaciones'
        })

@login_required
@require_POST
def ajax_update_profile(request):
    """Actualizar perfil del padre"""
    try:
        user = request.user
        
        # Actualizar campos básicos
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        
        # Campos adicionales si existen
        if hasattr(user, 'phone'):
            user.phone = request.POST.get('phone', getattr(user, 'phone', ''))
        if hasattr(user, 'address'):
            user.address = request.POST.get('address', getattr(user, 'address', ''))
        
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Perfil actualizado correctamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al actualizar perfil'
        })

@login_required
@require_GET
def ajax_export_child_report(request, child_id):
    """Exportar reporte de un hijo (simulado)"""
    try:
        child = Child.objects.get(id=child_id, parent=request.user)
        
        # En un sistema real, aquí generarías un PDF
        # Por ahora, devolvemos un JSON con los datos
        report_data = {
            'child_name': child.name,
            'grade': child.grade,
            'report_date': timezone.now().strftime('%d/%m/%Y'),
            'courses': [],
            'assignments': [],
            'grades': []
        }
        
        # Obtener datos del hijo
        courses = Course.objects.filter(student=child)
        for course in courses:
            course_data = {
                'name': course.name,
                'teacher': course.teacher.get_full_name(),
                'progress': random.randint(60, 95),
                'assignments_count': course.assignments.count()
            }
            report_data['courses'].append(course_data)
        
        return JsonResponse({
            'success': True,
            'report': report_data,
            'message': 'Reporte generado correctamente'
        })
    except Child.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Hijo no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al generar reporte'
        })

@require_POST
@login_required
def ajax_add_child(request):
    """Vincular un hijo existente (usuario estudiante) al padre"""
    try:
        username = request.POST.get('student_username', '').strip()
        fullname = request.POST.get('student_fullname', '').strip()
        email = request.POST.get('student_email', '').strip()

        if not all([username, fullname, email]):
            return JsonResponse({
                'success': False,
                'error': 'Todos los campos son obligatorios.'
            })

        # Buscar usuario estudiante
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            student = User.objects.get(username=username, email=email, user_type=1)
            # Verificar nombre completo
            full_name_db = f"{student.first_name} {student.last_name}".strip().lower()
            if fullname.lower() != full_name_db:
                return JsonResponse({
                    'success': False,
                    'error': 'El nombre completo no coincide con el usuario y correo proporcionados.'
                })
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'No se encontró un estudiante con esos datos.'
            })

        # Vincular al padre
        if hasattr(request.user, 'parent_profile'):
            request.user.parent_profile.children.add(student)
            request.user.parent_profile.save()
        else:
            return JsonResponse({
                'success': False,
                'error': 'El usuario actual no tiene perfil de padre/madre.'
            })

        return JsonResponse({
            'success': True,
            'message': 'Hijo vinculado correctamente.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al vincular hijo: {str(e)}'
        })

# Endpoints mínimos para AJAX dashboard padre
@login_required
@require_GET
def ajax_recent_activities(request):
    return JsonResponse({'success': True, 'activities': []})

@login_required
@require_GET
def ajax_dashboard_stats(request):
    return JsonResponse({'success': True, 'stats': {}})

@login_required
@require_GET
def ajax_notifications(request):
    return JsonResponse({'success': True, 'notifications': []})

@login_required
@require_GET
def ajax_children_list(request):
    children = []
    if hasattr(request.user, 'parent_profile'):
        children = request.user.parent_profile.children.all()
    html = render_to_string('dashboards/partials/parent_children_list.html', {'children': children})
    return JsonResponse({'success': True, 'children': list(children.values('id', 'first_name', 'last_name', 'email', 'username')), 'html': html})

# ... existing code ...