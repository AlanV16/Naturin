from django.db import models
from django.conf import settings
from apps.common.models import Category, Location

class MultimediaCard(models.Model):
    """Ficha multimedia educativa para especies"""
    
    MEDIA_TYPE_CHOICES = [
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('image', 'Imagen'),
        ('document', 'Documento'),
        ('interactive', 'Interactivo'),
    ]
    
    EDUCATIONAL_LEVEL_CHOICES = [
        ('primaria', 'Primaria'),
        ('secundaria', 'Secundaria'),
        ('universidad', 'Universidad'),
        ('general', 'General'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Título")
    description = models.TextField(verbose_name="Descripción")
    
    # Tipo de contenido multimedia
    media_type = models.CharField(
        max_length=20, 
        choices=MEDIA_TYPE_CHOICES, 
        verbose_name="Tipo de medio"
    )
    
    # Archivos multimedia
    video_file = models.FileField(
        upload_to='multimedia/videos/', 
        blank=True, 
        null=True, 
        verbose_name="Archivo de video"
    )
    audio_file = models.FileField(
        upload_to='multimedia/audio/', 
        blank=True, 
        null=True, 
        verbose_name="Archivo de audio"
    )
    image_file = models.ImageField(
        upload_to='multimedia/images/', 
        blank=True, 
        null=True, 
        verbose_name="Imagen"
    )
    document_file = models.FileField(
        upload_to='multimedia/documents/', 
        blank=True, 
        null=True, 
        verbose_name="Documento"
    )
    
    # URL externa para contenido interactivo o embebido
    external_url = models.URLField(
        blank=True, 
        null=True, 
        verbose_name="URL externa"
    )
    
    # Metadatos educativos
    educational_level = models.CharField(
        max_length=20,
        choices=EDUCATIONAL_LEVEL_CHOICES,
        default='general',
        verbose_name="Nivel educativo"
    )
    
    subject_area = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Área temática"
    )
    
    learning_objectives = models.TextField(
        blank=True, 
        verbose_name="Objetivos de aprendizaje"
    )
    
    duration = models.PositiveIntegerField(
        blank=True, 
        null=True, 
        verbose_name="Duración (minutos)"
    )
    
    # Relaciones
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='multimedia_cards',
        verbose_name="Categoría"
    )
    
    locations = models.ManyToManyField(
        Location,
        related_name='multimedia_cards',
        blank=True,
        verbose_name="Ubicaciones relacionadas"
    )
    
    # Autor y control de versiones
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='multimedia_cards',
        verbose_name="Autor"
    )
    
    is_public = models.BooleanField(
        default=True, 
        verbose_name="Público"
    )
    
    is_featured = models.BooleanField(
        default=False, 
        verbose_name="Destacado"
    )
    
    # Estadísticas
    views_count = models.PositiveIntegerField(
        default=0, 
        verbose_name="Número de vistas"
    )
    
    downloads_count = models.PositiveIntegerField(
        default=0, 
        verbose_name="Número de descargas"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Fecha de creación"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="Última actualización"
    )
    
    class Meta:
        verbose_name = "Ficha multimedia"
        verbose_name_plural = "Fichas multimedia"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_media_file(self):
        """Retorna el archivo multimedia principal según el tipo"""
        if self.media_type == 'video' and self.video_file:
            return self.video_file
        elif self.media_type == 'audio' and self.audio_file:
            return self.audio_file
        elif self.media_type == 'image' and self.image_file:
            return self.image_file
        elif self.media_type == 'document' and self.document_file:
            return self.document_file
        return None
    
    def increment_views(self):
        """Incrementa el contador de vistas"""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def increment_downloads(self):
        """Incrementa el contador de descargas"""
        self.downloads_count += 1
        self.save(update_fields=['downloads_count'])


class MultimediaTag(models.Model):
    """Etiquetas para organizar fichas multimedia"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Nombre")
    color = models.CharField(max_length=7, default="#007bff", verbose_name="Color")
    
    class Meta:
        verbose_name = "Etiqueta multimedia"
        verbose_name_plural = "Etiquetas multimedia"
    
    def __str__(self):
        return self.name


class MultimediaCardTag(models.Model):
    """Relación muchos a muchos entre fichas multimedia y etiquetas"""
    multimedia_card = models.ForeignKey(MultimediaCard, on_delete=models.CASCADE)
    tag = models.ForeignKey(MultimediaTag, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ['multimedia_card', 'tag']
