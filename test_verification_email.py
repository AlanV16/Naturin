#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NatureIn.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.users.utils import send_verification_email

User = get_user_model()

def test_verification_email():
    """Prueba el sistema de verificación de email"""
    print("=== Prueba de Verificación de Email ===")
    
    # Crear un usuario de prueba
    try:
        # Verificar si el usuario ya existe
        test_user, created = User.objects.get_or_create(
            email='test_verification@example.com',
            defaults={
                'username': 'test_verification',
                'first_name': 'Test',
                'last_name': 'Verification',
                'user_type': 1,  # Estudiante
                'is_active': False,
                'is_email_verified': False,
            }
        )
        
        if created:
            test_user.set_password('testpass123')
            test_user.save()
            print(f"✅ Usuario de prueba creado: {test_user.email}")
        else:
            print(f"📝 Usuario de prueba ya existe: {test_user.email}")
        
        # Generar código de verificación
        verification_code = test_user.generate_verification_code()
        print(f"🔐 Código de verificación generado: {verification_code}")
        
        # Enviar email de verificación
        try:
            send_verification_email(test_user)
            print("✅ Email de verificación enviado correctamente")
            print("📧 Revisa la bandeja de entrada de test_verification@example.com")
        except Exception as e:
            print(f"❌ Error al enviar email de verificación: {e}")
        
        # Verificar el código
        is_valid = test_user.is_verification_code_valid(verification_code)
        print(f"🔍 Código válido: {is_valid}")
        
        if is_valid:
            test_user.verify_email()
            print("✅ Email verificado correctamente")
            print(f"📊 Estado del usuario: is_active={test_user.is_active}, is_email_verified={test_user.is_email_verified}")
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")

if __name__ == '__main__':
    test_verification_email() 