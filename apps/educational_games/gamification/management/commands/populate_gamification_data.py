from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.educational_games.gamification.models import (
    TipoActividad, TipoJuego, Insignias, Desafios, ConfiguracionGamificacion
)

class Command(BaseCommand):
    help = 'Pobla datos iniciales para el sistema de gamificación'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando población de datos de gamificación...')
        
        # Crear tipos de actividades
        self.create_tipos_actividad()
        
        # Crear tipos de juegos
        self.create_tipos_juego()
        
        # Crear insignias
        self.create_insignias()
        
        # Crear desafíos
        self.create_desafios()
        
        # Crear configuraciones
        self.create_configuraciones()
        
        self.stdout.write(
            self.style.SUCCESS('Datos de gamificación poblados exitosamente!')
        )

    def create_tipos_actividad(self):
        """Crear tipos de actividades básicos"""
        tipos = [
            'Cuestionario',
            'Exploración',
            'Investigación',
            'Proyecto',
            'Presentación',
            'Debate',
            'Experimento',
            'Observación',
            'Documentación',
            'Análisis'
        ]
        
        for tipo in tipos:
            TipoActividad.objects.get_or_create(TipoActividad=tipo)
        
        self.stdout.write(f'✓ {len(tipos)} tipos de actividades creados')

    def create_tipos_juego(self):
        """Crear tipos de juegos básicos"""
        tipos = [
            (1, 'Cuestionario'),
            (2, 'Emparejamiento'),
            (3, 'Crucigrama'),
            (4, 'Rompecabezas'),
            (5, 'Memoria'),
            (6, 'Sopa de Letras'),
            (7, 'Ordenamiento'),
            (8, 'Identificación'),
            (9, 'Clasificación'),
            (10, 'Simulación')
        ]
        
        for id_tipo, nombre in tipos:
            TipoJuego.objects.get_or_create(
                IDtipoJuego=id_tipo,
                defaults={'TipoJuego': nombre}
            )
        
        self.stdout.write(f'✓ {len(tipos)} tipos de juegos creados')

    def create_insignias(self):
        """Crear insignias básicas"""
        insignias_data = [
            {
                'nombre': 'Primer Paso',
                'descripcion': 'Completa tu primera actividad',
                'tipo_insignia': 'first_activity',
                'puntos_requeridos': 10,
                'condicion': 'Completar 1 actividad'
            },
            {
                'nombre': 'Explorador Novato',
                'descripcion': 'Completa 5 actividades',
                'tipo_insignia': 'explorer',
                'puntos_requeridos': 50,
                'condicion': 'Completar 5 actividades'
            },
            {
                'nombre': 'Maestro de Cuestionarios',
                'descripcion': 'Completa 10 cuestionarios',
                'tipo_insignia': 'quiz_master',
                'puntos_requeridos': 100,
                'condicion': 'Completar 10 cuestionarios'
            },
            {
                'nombre': 'Puntuación Perfecta',
                'descripcion': 'Obtén 100% en un cuestionario',
                'tipo_insignia': 'perfect_score',
                'puntos_requeridos': 0,
                'condicion': 'Obtener 100% en cualquier actividad'
            },
            {
                'nombre': 'Racha de 3',
                'descripcion': 'Completa actividades 3 días seguidos',
                'tipo_insignia': 'streak_3',
                'puntos_requeridos': 30,
                'condicion': 'Actividad diaria por 3 días'
            },
            {
                'nombre': 'Experto en Especies',
                'descripcion': 'Completa actividades sobre 10 especies diferentes',
                'tipo_insignia': 'especies_expert',
                'puntos_requeridos': 200,
                'condicion': 'Actividades sobre 10 especies'
            },
            {
                'nombre': 'Conservacionista',
                'descripcion': 'Completa actividades sobre conservación',
                'tipo_insignia': 'conservationist',
                'puntos_requeridos': 150,
                'condicion': 'Actividades de conservación'
            },
            {
                'nombre': 'Coleccionista',
                'descripcion': 'Obtén 5 insignias diferentes',
                'tipo_insignia': 'collector',
                'puntos_requeridos': 300,
                'condicion': 'Obtener 5 insignias'
            }
        ]
        
        for data in insignias_data:
            Insignias.objects.get_or_create(
                nombre=data['nombre'],
                defaults=data
            )
        
        self.stdout.write(f'✓ {len(insignias_data)} insignias creadas')

    def create_desafios(self):
        """Crear desafíos básicos"""
        ahora = timezone.now()
        
        desafios_data = [
            {
                'nombre': 'Desafío Diario: Explorador',
                'descripcion': 'Completa una actividad de exploración hoy',
                'tipo_desafio': 'diario',
                'puntos': 20,
                'nivel_minimo': 1,
                'condicion': 'Actividad de exploración',
                'fecha_inicio': ahora,
                'fecha_fin': ahora + timezone.timedelta(days=1),
                'activo': True
            },
            {
                'nombre': 'Desafío Semanal: Investigador',
                'descripcion': 'Completa 5 actividades de investigación esta semana',
                'tipo_desafio': 'semanal',
                'puntos': 100,
                'nivel_minimo': 2,
                'condicion': '5 actividades de investigación',
                'fecha_inicio': ahora,
                'fecha_fin': ahora + timezone.timedelta(weeks=1),
                'activo': True
            },
            {
                'nombre': 'Desafío Especial: Maestro',
                'descripcion': 'Obtén 3 puntuaciones perfectas',
                'tipo_desafio': 'especial',
                'puntos': 200,
                'nivel_minimo': 3,
                'condicion': '3 puntuaciones perfectas',
                'fecha_inicio': ahora,
                'fecha_fin': ahora + timezone.timedelta(weeks=2),
                'activo': True
            }
        ]
        
        for data in desafios_data:
            Desafios.objects.get_or_create(
                nombre=data['nombre'],
                defaults=data
            )
        
        self.stdout.write(f'✓ {len(desafios_data)} desafíos creados')

    def create_configuraciones(self):
        """Crear configuraciones básicas del sistema"""
        configuraciones = [
            {
                'nombre_configuracion': 'puntos_por_actividad',
                'valor': '10',
                'descripcion': 'Puntos base por completar una actividad',
                'activo': True
            },
            {
                'nombre_configuracion': 'puntos_por_juego',
                'valor': '15',
                'descripcion': 'Puntos base por completar un juego',
                'activo': True
            },
            {
                'nombre_configuracion': 'puntos_bonus_perfecto',
                'valor': '5',
                'descripcion': 'Puntos bonus por puntuación perfecta',
                'activo': True
            },
            {
                'nombre_configuracion': 'puntos_racha_diaria',
                'valor': '3',
                'descripcion': 'Puntos bonus por mantener racha diaria',
                'activo': True
            },
            {
                'nombre_configuracion': 'nivel_maximo',
                'valor': '10',
                'descripcion': 'Nivel máximo alcanzable',
                'activo': True
            }
        ]
        
        for config in configuraciones:
            ConfiguracionGamificacion.objects.get_or_create(
                nombre_configuracion=config['nombre_configuracion'],
                defaults=config
            )
        
        self.stdout.write(f'✓ {len(configuraciones)} configuraciones creadas') 