#!/usr/bin/env python3
"""
Script de verificación de funcionalidades del dashboard
Ejecutar con: python test_check.py
"""

import os
import sys

def check_file_exists(filepath):
    """Verifica si un archivo existe"""
    return os.path.exists(filepath)

def check_file_content(filepath, search_text):
    """Verifica si un archivo contiene cierto texto"""
    if not check_file_exists(filepath):
        return False
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            return search_text in content
    except:
        return False

def main():
    print("=== VERIFICACION DE FUNCIONALIDADES DEL DASHBOARD ===")
    print()
    
    # Archivos principales a verificar
    files_to_check = [
        "apps/users/templates/dashboards/dashboard_student.html",
        "apps/users/templates/dashboards/dashboard_teacher.html",
        "apps/users/templates/class/class_student.html",
        "apps/users/templates/class/class_teacher.html",
        "static/js/dashboard_student.js",
        "static/js/dashboard_teacher.js",
        "static/css/dashboards/style_dashboard_student.css",
        "static/css/dashboards/style_dashboard_teacher.css"
    ]
    
    print("1. Verificando archivos principales...")
    found_files = 0
    for filepath in files_to_check:
        if check_file_exists(filepath):
            print(f"✓ {filepath}")
            found_files += 1
        else:
            print(f"✗ {filepath}")
    
    print()
    print("2. Verificando funcionalidades específicas...")
    
    # Verificar funcionalidades en dashboard estudiante
    if check_file_exists("apps/users/templates/dashboards/dashboard_student.html"):
        print("✓ Dashboard estudiante - Modal de perfil" if check_file_content("apps/users/templates/dashboards/dashboard_student.html", "showProfileModal") else "✗ Dashboard estudiante - Modal de perfil")
        print("✓ Dashboard estudiante - Unirse a clase" if check_file_content("apps/users/templates/dashboards/dashboard_student.html", "showJoinClassForm") else "✗ Dashboard estudiante - Unirse a clase")
        print("✓ Dashboard estudiante - Avatar upload" if check_file_content("apps/users/templates/dashboards/dashboard_student.html", "avatarInput") else "✗ Dashboard estudiante - Avatar upload")
    
    # Verificar funcionalidades en dashboard profesor
    if check_file_exists("apps/users/templates/dashboards/dashboard_teacher.html"):
        print("✓ Dashboard profesor - Modal de perfil" if check_file_content("apps/users/templates/dashboards/dashboard_teacher.html", "showProfileModal") else "✗ Dashboard profesor - Modal de perfil")
        print("✓ Dashboard profesor - Crear curso" if check_file_content("apps/users/templates/dashboards/dashboard_teacher.html", "showCreateCourseModal") else "✗ Dashboard profesor - Crear curso")
        print("✓ Dashboard profesor - Avatar upload" if check_file_content("apps/users/templates/dashboards/dashboard_teacher.html", "avatarInput") else "✗ Dashboard profesor - Avatar upload")
    
    # Verificar funcionalidades de chat
    if check_file_exists("apps/users/templates/class/class_student.html"):
        print("✓ Class student - Chat functionality" if check_file_content("apps/users/templates/class/class_student.html", "addMessageToChat") else "✗ Class student - Chat functionality")
        print("✓ Class student - AJAX chat" if check_file_content("apps/users/templates/class/class_student.html", "fetch") else "✗ Class student - AJAX chat")
    
    if check_file_exists("apps/users/templates/class/class_teacher.html"):
        print("✓ Class teacher - Chat functionality" if check_file_content("apps/users/templates/class/class_teacher.html", "addMessageToChat") else "✗ Class teacher - Chat functionality")
        print("✓ Class teacher - AJAX chat" if check_file_content("apps/users/templates/class/class_teacher.html", "fetch") else "✗ Class teacher - AJAX chat")
    
    print()
    print("=== RESUMEN ===")
    print(f"Archivos encontrados: {found_files}/{len(files_to_check)}")
    
    print()
    print("=== INSTRUCCIONES PARA EJECUTAR ===")
    print("1. Asegúrate de estar en el directorio raíz del proyecto")
    print("2. Ejecuta: python manage.py runserver")
    print("3. Abre http://localhost:8000 en tu navegador")
    print("4. Prueba las funcionalidades manualmente:")
    print("   - Login como estudiante y profesor")
    print("   - Acceder a los dashboards")
    print("   - Probar modales de perfil")
    print("   - Unirse a clases")
    print("   - Probar chat en las clases")
    
    print()
    print("Script completado!")

if __name__ == "__main__":
    main() 