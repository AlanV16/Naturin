#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NatureIn.settings')
django.setup()

from apps.users.models import Achievement

def create_achievements():
    """Crear logros de ejemplo"""
    achievements_data = [
        {
            'name': 'Primer Paso',
            'description': 'Completa tu primera lección sobre biodiversidad',
            'icon': 'star-fill',
            'points': 10
        },
        {
            'name': 'Explorador Novato',
            'description': 'Identifica 5 especies diferentes en el mapa interactivo',
            'icon': 'binoculars',
            'points': 25
        },
        {
            'name': 'Guardián del Bosque',
            'description': 'Completa 10 actividades de conservación',
            'icon': 'tree-fill',
            'points': 50
        },
        {
            'name': 'Experto en Fauna',
            'description': 'Obtén puntuación perfecta en 3 cuestionarios sobre animales',
            'icon': 'award-fill',
            'points': 75
        }
    ]
    
    created_count = 0
    for data in achievements_data:
        achievement, created = Achievement.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
        if created:
            print(f'✓ Creado logro: {achievement.name} ({achievement.points} pts)')
            created_count += 1
        else:
            print(f'- Ya existe logro: {achievement.name}')
    
    print(f'\nResumen:')
    print(f'- Logros creados: {created_count}')
    print(f'- Total de logros en la base de datos: {Achievement.objects.count()}')

if __name__ == '__main__':
    create_achievements()
