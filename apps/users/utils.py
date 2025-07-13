import os
import random
import string
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from .models import User, Achievement, StudentAchievement
from apps.educational_games.gamification.models import Classroom, ClassroomStudent, Activities, ActivityType, GameType, Levels
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site
import logging


logger = logging.getLogger(__name__)

def send_verification_email(user):
    """Envía email de verificación con código"""
    try:
        # Generar código de verificación
        verification_code = user.generate_verification_code()
        
        # Preparar contexto para el template
        context = {
            'user': user,
            'verification_code': verification_code,
            'site_name': 'NatureIn - Plataforma Educativa',
        }
        
        # Renderizar template HTML (usar ruta correcta)
        html_message = render_to_string('emails/verification_email.html', context)
        plain_message = strip_tags(html_message)
        
        # Enviar email
        send_mail(
            subject='Verifica tu cuenta - Código de verificación',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email de verificación enviado a {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando email de verificación: {str(e)}")
        print(f"Error enviando email: {e}")  # Para debugging
        return False

def send_welcome_email(user):
    """Envía email de bienvenida después de la verificación"""
    try:
        context = {
            'user': user,
            'site_name': 'Tu Plataforma Educativa',
        }
        
        html_message = render_to_string('emails/welcome_email.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject='¡Bienvenido a nuestra plataforma!',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email de bienvenida enviado a {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando email de bienvenida: {str(e)}")
        return False


def send_password_reset_email(user):
    """
    Envía un email con el código para restablecer la contraseña
    """
    try:
        # Generar código de reset
        reset_code = user.generate_password_reset_code()
        
        # Obtener el sitio actual
        try:
            site = Site.objects.get_current()
            site_name = site.name
        except:
            site_name = "NatureIn"
        
        # Preparar contexto para el template
        context = {
            'user': user,
            'reset_code': reset_code,
            'site_name': site_name,
        }
        
        # Renderizar el template del email
        html_message = render_to_string('emails/password_reset_email.html', context)
        plain_message = f"""
Hola {user.first_name},

Has solicitado restablecer tu contraseña en {site_name}.

Tu código de verificación es: {reset_code}

Este código expira en 15 minutos.

Si no solicitaste este cambio, ignora este email.

Equipo de {site_name}
        """
        
        # Enviar email
        send_mail(
            subject=f'{site_name} - Restablecer Contraseña',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email de reset de contraseña enviado a {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando email de reset: {str(e)}")
        return False
    
def get_user_courses(user):
    if user.user_type == 1:  # Estudiante
        return Classroom.objects.filter(
            classroomstudent__student=user,
            status='active'
        ).select_related('teacher').prefetch_related('activities')
    elif user.user_type == 2:  # Profesor
        return Classroom.objects.filter(
            teacher=user,
            status='active'
        ).prefetch_related('classroomstudent_set', 'activities')
    return None

def get_user_achievements(user):
    return StudentAchievement.objects.filter(
        student=user
    ).select_related('achievement').order_by('-earned_at')

def get_user_global_progress(user):
    classroom_students = ClassroomStudent.objects.filter(student=user)
    total_actividades = Activities.objects.filter(classroom__in=classroom_students.values('classroom')).count()
    actividades_completadas = Activities.objects.filter(
        classroom__in=classroom_students.values('classroom'),
        completadas__student=user
    ).count()
    
    if total_actividades > 0:
        return (actividades_completadas / total_actividades) * 100
    return 0

def get_class_activities(classroom):
    return Activities.objects.filter(
        classroom=classroom,
        status='active'
    ).order_by('created_at')

def get_class_content(classroom):
    return classroom.content_set.filter(
        status='active'
    ).order_by('order')

def get_student_class_progress(user, classroom):
    total_actividades = classroom.activities.count()
    completadas = classroom.activities.filter(
        completadas__student=user
    ).count()
    
    if total_actividades > 0:
        return (completadas / total_actividades) * 100
    return 0

def get_student_class_badges(user, classroom):
    return StudentAchievement.objects.filter(
        student=user,
        achievement__classroom=classroom
    ).select_related('achievement')

def get_student_class_achievements(user, classroom):
    return StudentAchievement.objects.filter(
        student=user,
        achievement__classroom=classroom
    ).select_related('achievement')

def get_class_chat_messages(classroom, limit=50):
    return classroom.messages.filter(
        status='active'
    ).select_related('user').order_by('-created_at')[:limit]

def get_user_level(user):
    total_points = StudentAchievement.objects.filter(
        student=user
    ).aggregate(
        total_points=Sum('achievement__points')
    )['total_points'] or 0
    
    return Levels.objects.filter(
        points_required__lte=total_points
    ).order_by('-points_required').first()

def get_user_points(user):
    return StudentAchievement.objects.filter(
        student=user
    ).aggregate(
        total_points=Sum('achievement__points')
    )['total_points'] or 0

def get_class_achievements(classroom):
    return StudentAchievement.objects.filter(
        student=user,
        achievement__classroom=classroom
    ).aggregate(
        class_points=Sum('achievement__points')
    )['class_points'] or 0

def generate_unique_class_code():
    """Generar código único para clase"""
    attempts = 0
    max_attempts = 100
    
    while Classroom.objects.filter(code=code).exists() and attempts < max_attempts:
        letters = ''.join(random.choices(string.ascii_uppercase, k=3))
        numbers = ''.join(random.choices(string.digits, k=3))
        code = letters + numbers
        attempts += 1
    
    return code
