#!/usr/bin/env python
import os

def create_env_file():
    """Crea el archivo .env con las credenciales de email"""
    env_content = """# Configuración de Email
EMAIL_HOST_USER=natureinsoporte@gmail.com
EMAIL_HOST_PASSWORD=vpspklzkvqxnzsav
DEFAULT_FROM_EMAIL=natureinsoporte@gmail.com

# Configuración de Django
SECRET_KEY=django-insecure-your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Archivo .env creado correctamente")
    print("📧 Credenciales de email configuradas:")
    print("   - Usuario: natureinsoporte@gmail.com")
    print("   - Contraseña: vpspklzkvqxnzsav")
    print("   - Remitente: natureinsoporte@gmail.com")

if __name__ == '__main__':
    create_env_file() 