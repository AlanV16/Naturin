from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.gamification.models import Notification
from datetime import datetime, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea notificaciones de prueba para usuarios'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Nombre de usuario para crear notificaciones')
        parser.add_argument('--count', type=int, default=5, help='Número de notificaciones a crear')

    def handle(self, *args, **options):
        username = options['username']
        count = options['count']
        
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Usuario "{username}" no encontrado')
                )
                return
        else:
            # Usar el primer usuario disponible
            user = User.objects.first()
            if not user:
                self.stdout.write(
                    self.style.ERROR('No hay usuarios en el sistema')
                )
                return
        
        # Tipos de notificaciones de prueba
        test_notifications = [
            {
                'notification_type': 'activity_completed',
                'title': 'Actividad Completada',
                'message': 'El estudiante Juan Pérez ha completado la actividad "Identificación de Especies"'
            },
            {
                'notification_type': 'quiz_completed',
                'title': 'Quiz Completado',
                'message': 'María García ha terminado el quiz sobre biodiversidad con 85% de aciertos'
            },
            {
                'notification_type': 'achievement_unlocked',
                'title': 'Logro Desbloqueado',
                'message': 'Carlos López ha desbloqueado el logro "Explorador Naturalista"'
            },
            {
                'notification_type': 'level_up',
                'title': 'Subida de Nivel',
                'message': 'Ana Rodríguez ha subido al nivel 5 en el módulo de ecología'
            },
            {
                'notification_type': 'trivia_completed',
                'title': 'Trivia Completada',
                'message': 'Luis Martínez ha completado la trivia sobre conservación ambiental'
            }
        ]
        
        created_count = 0
        for i in range(min(count, len(test_notifications))):
            notification_data = test_notifications[i]
            
            # Crear notificación con fecha escalonada
            created_at = datetime.now() - timedelta(hours=i)
            
            notification = Notification.objects.create(
                recipient=user,
                notification_type=notification_data['notification_type'],
                title=notification_data['title'],
                message=notification_data['message'],
                is_read=i % 2 == 0,  # Alternar entre leídas y no leídas
                created_at=created_at
            )
            created_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Notificación creada: {notification.title}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Se crearon {created_count} notificaciones para el usuario {user.username}')
        ) 