from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.common.models import Category, Location
from apps.multimedia.models import MultimediaCard, MultimediaTag
from django.core.files.base import ContentFile
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea datos de muestra para las fichas multimedia'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creando datos de muestra...'))
        
        # Crear categorías
        categories_data = [
            {
                'name': 'Aves',
                'description': 'Especies de aves y pájaros de diferentes hábitats'
            },
            {
                'name': 'Mamíferos',
                'description': 'Mamíferos terrestres y marinos'
            },
            {
                'name': 'Reptiles',
                'description': 'Serpientes, lagartos, tortugas y otros reptiles'
            },
            {
                'name': 'Anfibios',
                'description': 'Ranas, sapos, salamandras y otros anfibios'
            },
            {
                'name': 'Peces',
                'description': 'Especies de peces de agua dulce y salada'
            },
            {
                'name': 'Insectos',
                'description': 'Insectos, arañas y otros artrópodos'
            },
            {
                'name': 'Plantas',
                'description': 'Árboles, flores, hierbas y otras plantas'
            },
            {
                'name': 'Ecosistemas',
                'description': 'Hábitats y ecosistemas completos'
            },
            {
                'name': 'Conservación',
                'description': 'Especies en peligro y esfuerzos de conservación'
            },
            {
                'name': 'Educación Ambiental',
                'description': 'Contenido educativo sobre medio ambiente'
            }
        ]
        
        categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories.append(category)
            if created:
                self.stdout.write(f'Categoría creada: {category.name}')
            else:
                self.stdout.write(f'Categoría ya existe: {category.name}')
        
        # Crear ubicaciones
        locations_data = [
            {
                'name': 'Amazonas',
                'description': 'Selva amazónica',
                'latitude': -3.4653,
                'longitude': -58.3804
            },
            {
                'name': 'Andes',
                'description': 'Cordillera de los Andes',
                'latitude': -13.1631,
                'longitude': -72.5450
            },
            {
                'name': 'Galápagos',
                'description': 'Islas Galápagos',
                'latitude': -0.7773,
                'longitude': -91.1426
            },
            {
                'name': 'Pacífico',
                'description': 'Océano Pacífico',
                'latitude': 0.0000,
                'longitude': -160.0000
            },
            {
                'name': 'Caribe',
                'description': 'Mar Caribe',
                'latitude': 15.0000,
                'longitude': -75.0000
            },
            {
                'name': 'Páramo',
                'description': 'Ecosistema de páramo',
                'latitude': 0.0000,
                'longitude': -78.0000
            },
            {
                'name': 'Manglar',
                'description': 'Ecosistema de manglar',
                'latitude': 1.0000,
                'longitude': -79.0000
            },
            {
                'name': 'Bosque Seco',
                'description': 'Bosque seco tropical',
                'latitude': -2.0000,
                'longitude': -80.0000
            }
        ]
        
        locations = []
        for loc_data in locations_data:
            location, created = Location.objects.get_or_create(
                name=loc_data['name'],
                defaults={
                    'description': loc_data['description'],
                    'latitude': loc_data['latitude'],
                    'longitude': loc_data['longitude']
                }
            )
            locations.append(location)
            if created:
                self.stdout.write(f'Ubicación creada: {location.name}')
            else:
                self.stdout.write(f'Ubicación ya existe: {location.name}')
        
        # Crear etiquetas multimedia
        tags_data = [
            {'name': 'Educativo', 'color': '#28a745'},
            {'name': 'Interactivo', 'color': '#007bff'},
            {'name': 'Conservación', 'color': '#dc3545'},
            {'name': 'Biodiversidad', 'color': '#17a2b8'},
            {'name': 'Endémico', 'color': '#ffc107'},
            {'name': 'Marino', 'color': '#6f42c1'},
            {'name': 'Terrestre', 'color': '#fd7e14'},
            {'name': 'Primaria', 'color': '#e83e8c'},
            {'name': 'Secundaria', 'color': '#20c997'},
            {'name': 'Universidad', 'color': '#6c757d'}
        ]
        
        tags = []
        for tag_data in tags_data:
            tag, created = MultimediaTag.objects.get_or_create(
                name=tag_data['name'],
                defaults={'color': tag_data['color']}
            )
            tags.append(tag)
            if created:
                self.stdout.write(f'Etiqueta creada: {tag.name}')
            else:
                self.stdout.write(f'Etiqueta ya existe: {tag.name}')
        
        # Crear usuario de prueba si no existe
        try:
            user = User.objects.get(username='admin')
        except User.DoesNotExist:
            user = User.objects.create_user(
                username='admin',
                email='admin@example.com',
                password='admin123',
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write('Usuario admin creado')
        
        # Crear fichas multimedia de ejemplo
        multimedia_data = [
            {
                'title': 'El Colibrí Esmeralda: Joya de los Andes',
                'description': 'Descubre la fascinante vida del colibrí esmeralda, una especie endémica de los Andes ecuatorianos. Este video educativo muestra su comportamiento, hábitat y la importancia de su conservación.',
                'media_type': 'video',
                'educational_level': 'primaria',
                'subject_area': 'Biología, Conservación',
                'learning_objectives': 'Identificar características del colibrí esmeralda, comprender su hábitat natural y reconocer la importancia de la conservación de especies endémicas.',
                'duration': 15,
                'category': 'Aves',
                'locations': ['Andes'],
                'is_featured': True
            },
            {
                'title': 'Sonidos de la Selva Amazónica',
                'description': 'Una experiencia auditiva inmersiva que te transporta al corazón de la selva amazónica. Escucha los sonidos de monos, aves, insectos y otros animales en su hábitat natural.',
                'media_type': 'audio',
                'educational_level': 'secundaria',
                'subject_area': 'Ecología, Biología',
                'learning_objectives': 'Reconocer diferentes sonidos de la fauna amazónica, comprender la biodiversidad acústica y apreciar la complejidad de los ecosistemas.',
                'duration': 25,
                'category': 'Ecosistemas',
                'locations': ['Amazonas'],
                'is_featured': True
            },
            {
                'title': 'Guía Visual: Tortugas de Galápagos',
                'description': 'Una completa guía visual con imágenes de alta calidad de las diferentes especies de tortugas que habitan en las Islas Galápagos. Incluye información sobre su evolución y adaptaciones únicas.',
                'media_type': 'image',
                'educational_level': 'universidad',
                'subject_area': 'Biología Evolutiva, Zoología',
                'learning_objectives': 'Identificar las diferentes especies de tortugas de Galápagos, comprender el proceso de evolución por selección natural y analizar las adaptaciones específicas.',
                'duration': 10,
                'category': 'Reptiles',
                'locations': ['Galápagos'],
                'is_featured': False
            },
            {
                'title': 'Manual de Conservación Marina',
                'description': 'Documento completo sobre las mejores prácticas para la conservación de ecosistemas marinos. Incluye casos de estudio, metodologías y recomendaciones para educadores.',
                'media_type': 'document',
                'educational_level': 'universidad',
                'subject_area': 'Conservación Marina, Educación',
                'learning_objectives': 'Comprender los principios de conservación marina, aplicar metodologías de educación ambiental y desarrollar proyectos de conservación.',
                'duration': 45,
                'category': 'Conservación',
                'locations': ['Pacífico', 'Caribe'],
                'is_featured': True
            },
            {
                'title': 'Simulador Interactivo: Cadena Alimenticia',
                'description': 'Simulador interactivo que permite a los estudiantes experimentar con diferentes escenarios de cadena alimenticia en ecosistemas marinos. Aprende sobre las relaciones tróficas de manera divertida.',
                'media_type': 'interactive',
                'educational_level': 'secundaria',
                'subject_area': 'Ecología, Biología',
                'learning_objectives': 'Comprender las relaciones tróficas, analizar el impacto de cambios en la cadena alimenticia y desarrollar pensamiento crítico sobre ecosistemas.',
                'duration': 30,
                'category': 'Educación Ambiental',
                'locations': ['Pacífico'],
                'is_featured': False
            },
            {
                'title': 'Biodiversidad del Páramo',
                'description': 'Explora la rica biodiversidad del ecosistema de páramo a través de este documental educativo. Descubre las plantas y animales únicos que habitan en estas alturas.',
                'media_type': 'video',
                'educational_level': 'primaria',
                'subject_area': 'Biología, Geografía',
                'learning_objectives': 'Identificar especies del páramo, comprender las adaptaciones a la altura y valorar la importancia de este ecosistema.',
                'duration': 20,
                'category': 'Ecosistemas',
                'locations': ['Páramo'],
                'is_featured': False
            }
        ]
        
        for mm_data in multimedia_data:
            # Obtener la categoría
            category = Category.objects.get(name=mm_data['category'])
            
            # Obtener las ubicaciones
            mm_locations = [Location.objects.get(name=loc) for loc in mm_data['locations']]
            
            # Crear la ficha multimedia
            multimedia_card = MultimediaCard.objects.create(
                title=mm_data['title'],
                description=mm_data['description'],
                media_type=mm_data['media_type'],
                educational_level=mm_data['educational_level'],
                subject_area=mm_data['subject_area'],
                learning_objectives=mm_data['learning_objectives'],
                duration=mm_data['duration'],
                category=category,
                author=user,
                is_public=True,
                is_featured=mm_data['is_featured'],
                external_url='https://example.com/sample-content'  # URL de ejemplo
            )
            
            # Agregar ubicaciones
            multimedia_card.locations.set(mm_locations)
            
            # Agregar algunas etiquetas
            if mm_data['is_featured']:
                multimedia_card.multimediacardtag_set.create(tag=tags[2])  # Conservación
            if mm_data['educational_level'] == 'primaria':
                multimedia_card.multimediacardtag_set.create(tag=tags[7])  # Primaria
            elif mm_data['educational_level'] == 'secundaria':
                multimedia_card.multimediacardtag_set.create(tag=tags[8])  # Secundaria
            elif mm_data['educational_level'] == 'universidad':
                multimedia_card.multimediacardtag_set.create(tag=tags[9])  # Universidad
            
            multimedia_card.multimediacardtag_set.create(tag=tags[0])  # Educativo
            
            self.stdout.write(f'Ficha multimedia creada: {multimedia_card.title}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Datos de muestra creados exitosamente:\n'
                f'• {len(categories)} categorías\n'
                f'• {len(locations)} ubicaciones\n'
                f'• {len(tags)} etiquetas\n'
                f'• {len(multimedia_data)} fichas multimedia\n'
                f'• Usuario admin (si no existía)\n\n'
                f'Ahora puedes probar el sistema de fichas multimedia con estos datos.'
            )
        ) 