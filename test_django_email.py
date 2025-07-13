#!/usr/bin/env python
import os
import django
from django.core.mail import send_mail
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NatureIn.settings')
django.setup()

def test_django_email():
    """Prueba el envío de email usando Django"""
    print("=== Prueba de Email con Django ===")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'No configurado'}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    # Probar envío de email
    try:
        send_mail(
            subject='Prueba de Email - NatureIn',
            message='Este es un email de prueba para verificar la configuración de Django.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['zelayamy@gmail.com'],
            fail_silently=False,
        )
        print("\n✅ Email enviado correctamente!")
        print("📧 Revisa tu bandeja de entrada en zelayamy@gmail.com")
    except Exception as e:
        print(f"\n❌ Error al enviar email: {e}")
        print("🔍 Verifica las credenciales de Gmail y la configuración SMTP")

if __name__ == '__main__':
    test_django_email() 