from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.educational_games.gamification.models import (
    Niveles, Insignias, ActivityType, GameType, 
    ConfiguracionGamificacion, Desafios
)
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Poblar datos iniciales de gamificación'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando población de datos de gamificación...')
        
        # Crear tipos de actividades
        self.create_activity_types()
        
        # Crear tipos de juegos
        self.create_game_types()
        
        # Crear insignias
        self.create_insignias()
        
        # Crear desafíos
        self.create_desafios()
        
        # Crear configuraciones de gamificación
        self.create_configuraciones()
        
        # Crear niveles para usuarios existentes
        self.create_niveles_for_users()
        
        self.stdout.write(
            self.style.SUCCESS('Datos de gamificación poblados exitosamente!')
        )

    def create_activity_types(self):
        """Crear tipos de actividades"""
        activity_types = [
            'Quiz',
            'Tarea',
            'Lectura',
            'Juego Educativo',
            'Test',
            'Ficha Educativa',
            'Proyecto',
            'Investigación',
            'Presentación',
            'Evaluación'
        ]
        
        for tipo in activity_types:
            ActivityType.objects.get_or_create(
                TipoActividad=tipo
            )
        
        self.stdout.write(f'✓ {len(activity_types)} tipos de actividades creados')

    def create_game_types(self):
        """Crear tipos de juegos"""
        game_types = [
            (1, 'Quiz'),
            (2, 'Memoria'),
            (3, 'Puzzle'),
            (4, 'Aventura'),
            (5, 'Simulación'),
            (6, 'Estrategia'),
            (7, 'Rol'),
            (8, 'Carrera'),
            (9, 'Rompecabezas'),
            (10, 'Educativo')
        ]
        
        for id_tipo, nombre in game_types:
            GameType.objects.get_or_create(
                IDtipoJuego=id_tipo,
                defaults={'TipoJuego': nombre}
            )
        
        self.stdout.write(f'✓ {len(game_types)} tipos de juegos creados')

    def create_insignias(self):
        """Crear insignias según el sistema de niveles"""
        insignias_data = [
            # Insignias por nivel
            {
                'nombre': 'Explorador',
                'descripcion': 'Has completado tus primeras actividades y comenzado tu viaje de aprendizaje',
                'condicion': 'Alcanzar Nivel 2 (20-50 puntos)',
                'puntos_requeridos': 20,
                'tipo_insignia': 'explorer'
            },
            {
                'nombre': 'Investigador',
                'descripcion': 'Has demostrado dedicación en tu investigación y aprendizaje',
                'condicion': 'Alcanzar Nivel 3 (50-100 puntos)',
                'puntos_requeridos': 50,
                'tipo_insignia': 'explorer'
            },
            {
                'nombre': 'Maestro',
                'descripcion': 'Has alcanzado un nivel avanzado de conocimiento y habilidad',
                'condicion': 'Alcanzar Nivel 4 (100-500 puntos)',
                'puntos_requeridos': 100,
                'tipo_insignia': 'conservationist'
            },
            {
                'nombre': 'Experto',
                'descripcion': 'Has demostrado dominio excepcional en múltiples áreas',
                'condicion': 'Alcanzar Nivel 5 (500+ puntos)',
                'puntos_requeridos': 500,
                'tipo_insignia': 'conservationist'
            },
            {
                'nombre': 'Leyenda',
                'descripcion': 'Has alcanzado el nivel más alto de maestría',
                'condicion': 'Alcanzar Nivel 6 (700+ puntos)',
                'puntos_requeridos': 700,
                'tipo_insignia': 'conservationist'
            },
            # Insignias especiales
            {
                'nombre': 'Primera Actividad',
                'descripcion': 'Completaste tu primera actividad en la plataforma',
                'condicion': 'Completar la primera actividad',
                'puntos_requeridos': 5,
                'tipo_insignia': 'first_activity'
            },
            {
                'nombre': 'Puntuación Perfecta',
                'descripcion': 'Obtuviste 100% en una evaluación',
                'condicion': 'Obtener 100% en cualquier evaluación',
                'puntos_requeridos': 0,
                'tipo_insignia': 'perfect_score'
            },
            {
                'nombre': 'Racha de 3',
                'descripcion': 'Completaste 3 actividades consecutivas',
                'condicion': 'Completar 3 actividades sin fallar',
                'puntos_requeridos': 0,
                'tipo_insignia': 'streak_3'
            },
            {
                'nombre': 'Racha de 7',
                'descripcion': 'Completaste 7 actividades consecutivas',
                'condicion': 'Completar 7 actividades sin fallar',
                'puntos_requeridos': 0,
                'tipo_insignia': 'streak_7'
            },
            {
                'nombre': 'Racha de 30',
                'descripcion': 'Completaste 30 actividades consecutivas',
                'condicion': 'Completar 30 actividades sin fallar',
                'puntos_requeridos': 0,
                'tipo_insignia': 'streak_30'
            }
        ]
        
        for data in insignias_data:
            Insignias.objects.get_or_create(
                nombre=data['nombre'],
                defaults={
                    'descripcion': data['descripcion'],
                    'condicion': data['condicion'],
                    'puntos_requeridos': data['puntos_requeridos'],
                    'tipo_insignia': data['tipo_insignia']
                }
            )
        
        self.stdout.write(f'✓ {len(insignias_data)} insignias creadas')

    def create_desafios(self):
        """Crear desafíos diarios y semanales"""
        desafios_data = [
            {
                'nombre': 'Explorador Diario',
                'descripcion': 'Completa al menos una actividad hoy',
                'puntos': 10,
                'nivel_minimo': 1,
                'tipo_desafio': 'diario',
                'condicion': 'Completar 1 actividad',
                'fecha_inicio': timezone.now(),
                'fecha_fin': timezone.now() + timedelta(days=1)
            },
            {
                'nombre': 'Investigador Semanal',
                'descripcion': 'Completa 5 actividades esta semana',
                'puntos': 50,
                'nivel_minimo': 2,
                'tipo_desafio': 'semanal',
                'condicion': 'Completar 5 actividades',
                'fecha_inicio': timezone.now(),
                'fecha_fin': timezone.now() + timedelta(days=7)
            },
            {
                'nombre': 'Maestro Mensual',
                'descripcion': 'Completa 20 actividades este mes',
                'puntos': 200,
                'nivel_minimo': 3,
                'tipo_desafio': 'especial',
                'condicion': 'Completar 20 actividades',
                'fecha_inicio': timezone.now(),
                'fecha_fin': timezone.now() + timedelta(days=30)
            }
        ]
        
        for data in desafios_data:
            Desafios.objects.get_or_create(
                nombre=data['nombre'],
                defaults={
                    'descripcion': data['descripcion'],
                    'puntos': data['puntos'],
                    'nivel_minimo': data['nivel_minimo'],
                    'tipo_desafio': data['tipo_desafio'],
                    'condicion': data['condicion'],
                    'fecha_inicio': data['fecha_inicio'],
                    'fecha_fin': data['fecha_fin'],
                    'activo': True
                }
            )
        
        self.stdout.write(f'✓ {len(desafios_data)} desafíos creados')

    def create_configuraciones(self):
        """Crear configuraciones del sistema de gamificación"""
        configuraciones = [
            {
                'nombre_configuracion': 'puntos_nivel_1',
                'valor': '5',
                'descripcion': 'Puntos por actividad en Nivel 1 (0-20 puntos)'
            },
            {
                'nombre_configuracion': 'puntos_nivel_2',
                'valor': '10',
                'descripcion': 'Puntos por actividad en Nivel 2 (20-50 puntos)'
            },
            {
                'nombre_configuracion': 'puntos_nivel_3',
                'valor': '15',
                'descripcion': 'Puntos por actividad en Nivel 3 (50-100 puntos)'
            },
            {
                'nombre_configuracion': 'puntos_nivel_4',
                'valor': '20',
                'descripcion': 'Puntos por actividad en Nivel 4 (100-500 puntos)'
            },
            {
                'nombre_configuracion': 'puntos_nivel_superior',
                'valor': '25',
                'descripcion': 'Puntos por actividad en niveles superiores (500+ puntos)'
            },
            {
                'nombre_configuracion': 'incremento_nivel_superior',
                'valor': '5',
                'descripcion': 'Incremento de puntos por nivel adicional en niveles superiores'
            },
            {
                'nombre_configuracion': 'puntos_racha_3',
                'valor': '15',
                'descripcion': 'Puntos bonus por racha de 3 actividades'
            },
            {
                'nombre_configuracion': 'puntos_racha_7',
                'valor': '50',
                'descripcion': 'Puntos bonus por racha de 7 actividades'
            },
            {
                'nombre_configuracion': 'puntos_racha_30',
                'valor': '200',
                'descripcion': 'Puntos bonus por racha de 30 actividades'
            },
            {
                'nombre_configuracion': 'puntos_perfect_score',
                'valor': '25',
                'descripcion': 'Puntos bonus por puntuación perfecta (100%)'
            }
        ]
        
        for config in configuraciones:
            ConfiguracionGamificacion.objects.get_or_create(
                nombre_configuracion=config['nombre_configuracion'],
                defaults={
                    'valor': config['valor'],
                    'descripcion': config['descripcion'],
                    'activo': True
                }
            )
        
        self.stdout.write(f'✓ {len(configuraciones)} configuraciones creadas')

    def create_niveles_for_users(self):
        """Crear niveles para usuarios existentes"""
        users = User.objects.all()
        created_count = 0
        
        for user in users:
            nivel, created = Niveles.objects.get_or_create(
                IDusuario=user,
                defaults={
                    'nivel': 1,
                    'puntos_acumulados': 0,
                    'fecha_actualizacion': timezone.now()
                }
            )
            if created:
                created_count += 1
        
        self.stdout.write(f'✓ Niveles creados para {created_count} usuarios') 