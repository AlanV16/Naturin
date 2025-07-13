#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NatureIn.settings')
django.setup()

from apps.educational_games.gamification.models import Classroom
from apps.users.models import User
from django.utils import timezone

def test_create_class():
    """Probar la creación de una clase y verificar el ID"""
    print("=== PRUEBA DE CREACIÓN DE CLASE ===")
    
    # Obtener un docente (asumiendo que existe)
    try:
        docente = User.objects.filter(user_type=2).first()
        if not docente:
            print("❌ No hay docentes en la base de datos")
            return
        
        print(f"✅ Docente encontrado: {docente.get_full_name()}")
        
        # Crear una nueva clase
        classroom = Classroom.objects.create(
            name="Clase de Prueba",
            code="TEST123",
            grade="1",
            section="A",
            description="Clase de prueba para verificar IDs",
            teacher=docente,
            created_at=timezone.now()
        )
        
        print(f"✅ Clase creada exitosamente:")
        print(f"   ID: {classroom.id}")
        print(f"   Nombre: {classroom.name}")
        print(f"   Código: {classroom.code}")
        print(f"   Docente: {classroom.teacher.get_full_name()}")
        
        # Verificar todas las clases
        print("\n=== TODAS LAS CLASES ===")
        classrooms = Classroom.objects.all().order_by('id')
        for c in classrooms:
            print(f"ID: {c.id} - {c.name} ({c.code})")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_create_class() 