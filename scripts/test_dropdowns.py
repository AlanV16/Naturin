#!/usr/bin/env python3
"""
Script de prueba para verificar que los dropdowns funcionan correctamente
"""

import os
import sys
import django
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NatureIn.settings')
django.setup()

User = get_user_model()

def test_dropdown_functionality():
    """
    Prueba la funcionalidad de los dropdowns
    """
    print("=== Prueba de Dropdowns ===")
    
    # Crear cliente de prueba
    client = Client()
    
    # Crear usuario de prueba
    user = User.objects.create_user(
        username='test_student',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='Student',
        user_type=1  # Estudiante
    )
    
    # Hacer login
    client.login(username='test_student', password='testpass123')
    
    # Probar dashboard del estudiante
    response = client.get(reverse('users:dashboard_student', kwargs={'user_id': user.id}))
    
    print(f"Status code: {response.status_code}")
    print(f"Template usado: {response.templates[0].name if response.templates else 'No template'}")
    
    # Verificar que el HTML contiene los elementos necesarios
    content = response.content.decode('utf-8')
    
    checks = [
        ('userDropdown', 'id="userDropdown"' in content),
        ('dropdown-toggle', 'dropdown-toggle' in content),
        ('dropdown-menu', 'dropdown-menu' in content),
        ('data-bs-toggle', 'data-bs-toggle="dropdown"' in content),
        ('Bootstrap CSS', 'bootstrap' in content),
        ('Bootstrap JS', 'bootstrap' in content),
        ('Dashboard JS', 'dashboard.js' in content),
    ]
    
    print("\n=== Verificación de elementos ===")
    for check_name, check_result in checks:
        status = "✓" if check_result else "✗"
        print(f"{status} {check_name}: {'OK' if check_result else 'FALTA'}")
    
    # Limpiar usuario de prueba
    user.delete()
    
    print("\n=== Prueba completada ===")

if __name__ == "__main__":
    test_dropdown_functionality()
