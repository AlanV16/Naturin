#!/usr/bin/env python
"""
Script de prueba para verificar el envío de emails
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NatureIn.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from apps.users.utils import send_verification_email
from apps.users.models import User

def test_email_sending():
    """Prueba el envío de email"""
    print("=== PRUEBA DE ENVÍO DE EMAIL ===")
    
    # Verificar configuración
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    # Usar un email diferente para evitar conflictos
    test_email = 'test.naturein@gmail.com'
    
    # Crear un usuario de prueba
    test_user, created = User.objects.get_or_create(
        username='test_user_email',
        defaults={
            'email': test_email,
            'first_name': 'Test',
            'last_name': 'User',
            'is_active': False,
            'is_email_verified': False
        }
    )
    
    if created:
        test_user.set_password('testpass123')
        test_user.save()
        print(f"Usuario de prueba creado: {test_user.email}")
    else:
        print(f"Usuario de prueba existente: {test_user.email}")
    
    # Generar código de verificación
    verification_code = test_user.generate_verification_code()
    print(f"Código generado: {verification_code}")
    
    # Probar envío de email
    try:
        success = send_verification_email(test_user)
        if success:
            print("✅ Email enviado exitosamente")
        else:
            print("❌ Error enviando email")
    except Exception as e:
        print(f"❌ Excepción al enviar email: {e}")
    
    # Probar envío directo
    try:
        send_mail(
            subject='Prueba de Email - NatureIn',
            message='Este es un email de prueba para verificar la configuración.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False,
        )
        print("✅ Email directo enviado exitosamente")
    except Exception as e:
        print(f"❌ Error en email directo: {e}")

if __name__ == '__main__':
    test_email_sending() 