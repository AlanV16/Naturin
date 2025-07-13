#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NatureIn.settings')
django.setup()

from apps.educational_games.gamification.models import Aulas

def check_aulas():
    """Verificar aulas existentes en la base de datos"""
    print("=== VERIFICACIÓN DE AULAS ===")
    
    # Obtener todas las aulas
    aulas = Aulas.objects.all()
    
    if not aulas.exists():
        print("❌ No hay aulas en la base de datos")
        return
    
    print(f"✅ Se encontraron {aulas.count()} aulas:")
    print()
    
    for aula in aulas:
        print(f"ID: {aula.IDaula}")
        print(f"Nombre: {aula.NombreAula}")
        print(f"Código: {aula.CodigoAula}")
        print(f"Docente: {aula.IDdocente.get_full_name() if aula.IDdocente else 'N/A'}")
        print(f"Fecha: {aula.FechaCreacion}")
        print("-" * 50)
    
    # Verificar específicamente el aula con ID 3
    try:
        aula_3 = Aulas.objects.get(IDaula=3)
        print(f"✅ El aula con ID 3 existe: {aula_3.NombreAula}")
    except Aulas.DoesNotExist:
        print("❌ El aula con ID 3 NO existe")
        print("IDs disponibles:", list(aulas.values_list('IDaula', flat=True)))

if __name__ == "__main__":
    check_aulas() 