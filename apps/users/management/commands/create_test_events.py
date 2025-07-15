from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from apps.users.models import User, Course, Assignment, CalendarEvent, Subject

class Command(BaseCommand):
    help = 'Crea eventos de prueba para el calendario'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID del usuario para crear eventos',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                self.stdout.write(f'Creando eventos para {user.get_full_name()} (ID: {user.id})')
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Usuario con ID {user_id} no encontrado'))
                return
        else:
            # Buscar el primer usuario disponible
            user = User.objects.filter(is_active=True).first()
            if not user:
                self.stdout.write(self.style.ERROR('No se encontraron usuarios'))
                return
            self.stdout.write(f'Usando usuario: {user.get_full_name()} (ID: {user.id})')

        # Crear algunos cursos si no existen
        subject, created = Subject.objects.get_or_create(
            name='Ciencias Naturales',
            defaults={'description': 'Materias relacionadas con la naturaleza'}
        )

        course, created = Course.objects.get_or_create(
            name='Biología Básica',
            defaults={
                'code': 'BIO001',
                'description': 'Curso de introducción a la biología',
                'teacher': user if user.user_type == 2 else User.objects.filter(user_type=2).first(),
                'subject': subject,
                'grade': '6to'
            }
        )

        # Obtener fechas para los próximos días
        today = timezone.now().date()
        
        events_data = [
            {
                'title': 'Clase de Fotosíntesis',
                'event_type': 'class',
                'description': 'Estudio del proceso de fotosíntesis en plantas',
                'days_offset': 1,
                'hour': 10,
                'minute': 0,
            },
            {
                'title': 'Tarea: Ecosistemas',
                'event_type': 'assignment', 
                'description': 'Entrega del proyecto sobre ecosistemas locales',
                'days_offset': 3,
                'hour': 23,
                'minute': 59,
            },
            {
                'title': 'Examen de Botánica',
                'event_type': 'exam',
                'description': 'Evaluación sobre estructura y función de las plantas',
                'days_offset': 7,
                'hour': 14,
                'minute': 0,
            },
            {
                'title': 'Taller de Microscopía',
                'event_type': 'workshop',
                'description': 'Práctica con microscopios para observar células',
                'days_offset': 10,
                'hour': 16,
                'minute': 30,
            },
            {
                'title': 'Reunión con Padres',
                'event_type': 'meeting',
                'description': 'Reunión para discutir el progreso académico',
                'days_offset': 14,
                'hour': 18,
                'minute': 0,
            },
            {
                'title': 'Recordatorio: Proyecto Final',
                'event_type': 'reminder',
                'description': 'Fecha límite para entregar el proyecto final se acerca',
                'days_offset': 21,
                'hour': 9,
                'minute': 0,
            }
        ]

        created_events = 0
        
        for event_data in events_data:
            # Calcular fecha y hora del evento
            event_date = today + timedelta(days=event_data['days_offset'])
            event_datetime = timezone.make_aware(
                datetime.combine(
                    event_date, 
                    datetime.min.time().replace(
                        hour=event_data['hour'], 
                        minute=event_data['minute']
                    )
                )
            )
            
            # Crear el evento si no existe
            event, created = CalendarEvent.objects.get_or_create(
                title=event_data['title'],
                start_date=event_datetime,
                defaults={
                    'user': user,
                    'created_by': user,
                    'course': course,
                    'description': event_data['description'],
                    'event_type': event_data['event_type'],
                    'end_date': event_datetime + timedelta(hours=1),
                    'location': 'Aula Virtual' if event_data['event_type'] == 'class' else '',
                }
            )
            
            if created:
                # Agregar el usuario como participante
                event.participants.add(user)
                created_events += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Evento creado: {event.title} - {event_datetime.strftime("%d/%m/%Y %H:%M")}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠ Evento ya existe: {event.title}'
                    )
                )

        # Crear también algunas tareas como eventos
        if user.user_type == 2:  # Si es docente, crear tareas
            assignment_data = [
                {
                    'title': 'Investigación sobre Biodiversidad',
                    'description': 'Investigar la biodiversidad de tu región y crear un reporte',
                    'days_offset': 5,
                },
                {
                    'title': 'Mapa Conceptual de Ecosistemas',
                    'description': 'Crear un mapa conceptual detallado sobre los tipos de ecosistemas',
                    'days_offset': 12,
                }
            ]

            for assign_data in assignment_data:
                due_date = today + timedelta(days=assign_data['days_offset'])
                due_datetime = timezone.make_aware(
                    datetime.combine(due_date, datetime.min.time().replace(hour=23, minute=59))
                )

                assignment, created = Assignment.objects.get_or_create(
                    title=assign_data['title'],
                    course=course,
                    defaults={
                        'description': assign_data['description'],
                        'due_date': due_datetime,
                        'created_by': user,
                        'max_points': 100.0,
                        'status': 'published'
                    }
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Tarea creada: {assignment.title} - Vence: {due_datetime.strftime("%d/%m/%Y")}'
                        )
                    )

        # Mostrar resumen
        total_events = CalendarEvent.objects.filter(user=user).count()
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'✓ Proceso completado'))
        self.stdout.write(f'📅 Eventos creados en esta ejecución: {created_events}')
        self.stdout.write(f'📅 Total de eventos para {user.get_full_name()}: {total_events}')
        self.stdout.write('\n🔍 Para verificar, accede al calendario en el dashboard del usuario')
        self.stdout.write(f'🌐 URL sugerida: /usuarios/calendario/ (como usuario ID: {user.id})')
