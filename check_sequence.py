#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NatureIn.settings')
django.setup()

from django.db import connection
from apps.educational_games.gamification.models import Aulas

def check_sequence():
    """Verificar la secuencia de IDs en la base de datos"""
    print("=== VERIFICACIÓN DE SECUENCIA ===")
    
    # Obtener todas las aulas ordenadas por ID
    aulas = Aulas.objects.all().order_by('IDaula')
    
    print("Aulas existentes:")
    for aula in aulas:
        print(f"  ID: {aula.IDaula} - {aula.NombreAula}")
    
    # Verificar si hay gaps en la secuencia
    ids = [aula.IDaula for aula in aulas]
    print(f"\nIDs encontrados: {ids}")
    
    if len(ids) > 0:
        expected_ids = list(range(1, max(ids) + 1))
        missing_ids = set(expected_ids) - set(ids)
        
        if missing_ids:
            print(f"❌ IDs faltantes: {sorted(missing_ids)}")
        else:
            print("✅ No hay gaps en la secuencia")
    
    # Verificar la secuencia de PostgreSQL
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT last_value FROM aulas_idaula_seq;")
            result = cursor.fetchone()
            if result:
                print(f"Último valor de la secuencia: {result[0]}")
    except Exception as e:
        print(f"Error al verificar secuencia: {e}")

if __name__ == "__main__":
    check_sequence() 