from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from .models import User, Achievement, StudentAchievement
from apps.educational_games.gamification.models import Aulas, AulaEstudiante, Actividades, Niveles
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site
import logging
import random
import string
from django.core.mail import get_connection
from datetime import timedelta


logger = logging.getLogger(__name__)

def generate_classroom_code():
    """Genera un código único para el aula de 6 caracteres alfanuméricos"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        # Verificar que no exista
        try:
            from apps.educational_games.gamification.models import Aulas
            if not Aulas.objects.filter(CodigoAula=code).exists():
                return code
        except ImportError:
            return code

def send_verification_email(user):
    """Envía email de verificación con HTML template"""
    try:
        # Generar código de verificación
        code = ''.join(random.choices(string.digits, k=6))
        user.email_verification_code = code
        user.email_verification_created = timezone.now()
        user.save()
        
        # Contexto para el template
        context = {
            'user': user,
            'code': code,
            'site_name': 'NatureIn',
            'expiry_minutes': 10
        }
        
        # Renderizar template HTML
        try:
            html_message = render_to_string('emails/verification_email.html', context)
            plain_message = strip_tags(html_message)
        except:
            # Fallback a mensaje de texto plano
            plain_message = f'''
Hola {user.get_full_name()},

¡Bienvenido a NatureIn!

Tu código de verificación es: {code}

Este código expira en 10 minutos.

Si no solicitaste este registro, puedes ignorar este mensaje.

Saludos,
Equipo NatureIn
            '''
            html_message = None
        
        # Enviar email
        result = send_mail(
            subject='Verificación de email - NatureIn',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email de verificación enviado a {user.email} - Resultado: {result}")
        return result > 0
        
    except Exception as e:
        logger.error(f"Error enviando email de verificación a {user.email}: {str(e)}")
        return False

def send_welcome_email(user):
    """Envía email de bienvenida"""
    try:
        context = {
            'user': user,
            'site_name': 'NatureIn',
            'login_url': 'https://naturein.com/login'  # Cambia por tu URL real
        }
        
        try:
            html_message = render_to_string('emails/welcome_email.html', context)
            plain_message = strip_tags(html_message)
        except:
            plain_message = f'''
Hola {user.get_full_name()},

¡Bienvenido a NatureIn!

Tu cuenta ha sido activada exitosamente.

Ya puedes empezar a explorar nuestra plataforma educativa.

Saludos,
Equipo NatureIn
            '''
            html_message = None
        
        result = send_mail(
            subject='¡Bienvenido a NatureIn!',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email de bienvenida enviado a {user.email}")
        return result > 0
        
    except Exception as e:
        logger.error(f"Error enviando email de bienvenida a {user.email}: {str(e)}")
        return False

def send_password_reset_email(user):
    """Envía email para reset de contraseña"""
    try:
        # Generar código de reset
        code = ''.join(random.choices(string.digits, k=6))
        user.password_reset_code = code
        user.password_reset_created = timezone.now()
        user.save()
        
        context = {
            'user': user,
            'code': code,
            'site_name': 'NatureIn',
            'expiry_minutes': 15
        }
        
        try:
            html_message = render_to_string('emails/password_reset_email.html', context)
            plain_message = strip_tags(html_message)
        except:
            plain_message = f'''
Hola {user.get_full_name()},

Has solicitado restablecer tu contraseña en NatureIn.

Tu código de verificación es: {code}

Este código expira en 15 minutos.

Si no solicitaste este cambio, ignora este mensaje.

Saludos,
Equipo NatureIn
            '''
            html_message = None
        
        result = send_mail(
            subject='Restablecer contraseña - NatureIn',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email de reset de contraseña enviado a {user.email}")
        return result > 0
        
    except Exception as e:
        logger.error(f"Error enviando email de reset a {user.email}: {str(e)}")
        return False

def test_email_connection():
    """Función para probar la conexión de email"""
    try:
        connection = get_connection()
        connection.open()
        connection.close()
        logger.info("Conexión de email exitosa")
        return True
    except Exception as e:
        logger.error(f"Error en conexión de email: {str(e)}")
        return False

def get_user_courses(user):
    if user.user_type == 1:  # Estudiante
        return Aulas.objects.filter(
            aulaestudiante__estudiante=user,
            estado='activo'
        ).select_related('profesor').prefetch_related('actividades')
    elif user.user_type == 2:  # Profesor
        return Aulas.objects.filter(
            profesor=user,
            estado='activo'
        ).prefetch_related('aulaestudiante_set', 'actividades')
    return None

def get_user_achievements(user):
    return StudentAchievement.objects.filter(
        student=user
    ).select_related('achievement').order_by('-earned_at')

def get_user_global_progress(user):
    aulas_inscritas = AulaEstudiante.objects.filter(estudiante=user)
    total_actividades = Actividades.objects.filter(aula__in=aulas_inscritas.values('aula')).count()
    actividades_completadas = Actividades.objects.filter(
        aula__in=aulas_inscritas.values('aula'),
        completadas__estudiante=user
    ).count()
    
    return {
        'total_actividades': total_actividades,
        'completadas': actividades_completadas,
        'porcentaje': (actividades_completadas / total_actividades * 100) if total_actividades > 0 else 0,
        'nivel_actual': get_user_level(user),
        'puntos_totales': get_user_points(user)
    }

def get_class_activities(classroom):
    return Actividades.objects.filter(
        aula=classroom,
        estado='activo'
    ).order_by('fecha_creacion')

def get_class_content(classroom):
    return classroom.contenido_set.filter(
        estado='activo'
    ).order_by('orden')

def get_student_class_progress(user, classroom):
    total_actividades = classroom.actividades.count()
    completadas = classroom.actividades.filter(
        completadas__estudiante=user
    ).count()
    
    return {
        'total_actividades': total_actividades,
        'completadas': completadas,
        'porcentaje': (completadas / total_actividades * 100) if total_actividades > 0 else 0,
        'puntos_clase': get_student_class_points(user, classroom)
    }

def get_student_class_badges(user, classroom):
    return StudentAchievement.objects.filter(
        student=user,
        achievement__aula=classroom
    ).select_related('achievement')

def get_class_chat_messages(classroom, limit=50):
    return classroom.mensajes.filter(
        estado='activo'
    ).select_related('usuario').order_by('-fecha_creacion')[:limit]

def get_user_level(user):
    puntos_totales = get_user_points(user)
    return Niveles.objects.filter(
        puntos_requeridos__lte=puntos_totales
    ).order_by('-puntos_requeridos').first()

def get_user_points(user):
    return StudentAchievement.objects.filter(
        student=user
    ).aggregate(
        total_points=Sum('achievement__points')
    )['total_points'] or 0

def get_student_class_points(user, classroom):
    return StudentAchievement.objects.filter(
        student=user,
        achievement__aula=classroom
    ).aggregate(
        class_points=Sum('achievement__points')
    )['class_points'] or 0
