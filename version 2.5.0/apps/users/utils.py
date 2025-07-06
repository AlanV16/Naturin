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