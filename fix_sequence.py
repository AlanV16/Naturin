#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NatureIn.settings')
django.setup()

from django.db import connection
from apps.educational_games.gamification.models import Aulas

def fix_sequence():
    """Arreglar la secuencia de IDs en la base de datos"""
    print("=== ARREGLANDO SECUENCIA DE IDs ===")
    
    try:
        with connection.cursor() as cursor:
            # Obtener el máximo ID actual
            cursor.execute("SELECT MAX(\"IDaula\") FROM gamification_aulas;")
            max_id = cursor.fetchone()[0]
            
            if max_id:
                print(f"ID máximo actual: {max_id}")
                
                # Resetear la secuencia al siguiente valor después del máximo
                cursor.execute(f"SELECT setval('gamification_aulas_idaula_seq', {max_id});")
                print(f"Secuencia reseteada a {max_id}")
                
                # Verificar el nuevo valor de la secuencia
                cursor.execute("SELECT last_value FROM gamification_aulas_idaula_seq;")
                new_value = cursor.fetchone()[0]
                print(f"Nuevo valor de la secuencia: {new_value}")
                
                print("✅ Secuencia arreglada exitosamente")
            else:
                print("❌ No hay aulas en la base de datos")
                
    except Exception as e:
        print(f"❌ Error al arreglar la secuencia: {e}")

if __name__ == "__main__":
    fix_sequence() 