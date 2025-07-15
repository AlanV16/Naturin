#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NatureIn.settings')
django.setup()

from apps.users.models import Achievement, StudentAchievement, User

def assign_sample_achievements():
    """Asignar algunos logros de ejemplo al usuario ID 2"""
    try:
        # Obtener el usuario ID 2
        user = User.objects.get(id=2)
        print(f'Usuario encontrado: {user.username} (ID: {user.id})')
        
        # Obtener los primeros 2 logros para asignarlos como obtenidos
        achievements = Achievement.objects.all()[:2]
        
        created_count = 0
        for achievement in achievements:
            student_achievement, created = StudentAchievement.objects.get_or_create(
                student=user,
                achievement=achievement
            )
            if created:
                print(f'✓ Logro asignado: {achievement.name} ({achievement.points} pts)')
                created_count += 1
            else:
                print(f'- Usuario ya tiene el logro: {achievement.name}')
        
        print(f'\nResumen:')
        print(f'- Logros asignados: {created_count}')
        print(f'- Total de logros del usuario: {user.achievements.count()}')
        
    except User.DoesNotExist:
        print('Error: Usuario con ID 2 no encontrado')

if __name__ == '__main__':
    assign_sample_achievements()
