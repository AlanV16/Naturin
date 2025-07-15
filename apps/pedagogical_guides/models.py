from django.db import models
from django.conf import settings
from apps.common.models import Category, Location
from django.core.validators import MinValueValidator, MaxValueValidator

class GuideCategory(models.Model):
    """Categorías para organizar las guías pedagógicas"""
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    color = models.CharField(max_length=7, default="#007bff", verbose_name="Color")
    icon = models.CharField(max_length=50, default="bi-file-earmark-text", verbose_name="Icono")
    
    class Meta:
        verbose_name = "Categoría de guía"
        verbose_name_plural = "Categorías de guías"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Guide(models.Model):
    """Guías pedagógicas mejoradas con fichas educativas y multimedia"""
    
    CONTENT_TYPE_CHOICES = [
        ('guide', 'Guía Pedagógica'),
        ('worksheet', 'Ficha Educativa'),
        ('multimedia', 'Ficha Multimedia'),
        ('interactive', 'Contenido Interactivo'),
    ]
    
    EDUCATIONAL_LEVEL_CHOICES = [
        ('primaria', 'Primaria'),
        ('secundaria', 'Secundaria'),
        ('universidad', 'Universidad'),
        ('general', 'General'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Título")
    description = models.TextField(verbose_name="Descripción")
    
    # Tipo de contenido
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default='guide',
        verbose_name="Tipo de contenido"
    )
    
    # Archivos multimedia
    pdf_file = models.FileField(
        upload_to='guides/pdfs/',
        blank=True,
        null=True,
        verbose_name="Archivo PDF"
    )
    word_file = models.FileField(
        upload_to='guides/word/',
        blank=True,
        null=True,
        verbose_name="Archivo Word"
    )
    video_file = models.FileField(
        upload_to='guides/videos/',
        blank=True,
        null=True,
        verbose_name="Archivo de video"
    )
    audio_file = models.FileField(
        upload_to='guides/audio/',
        blank=True,
        null=True,
        verbose_name="Archivo de audio"
    )
    image_file = models.ImageField(
        upload_to='guides/images/',
        blank=True,
        null=True,
        verbose_name="Imagen"
    )
    
    # URL externa para contenido interactivo
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
        GuideCategory,
        on_delete=models.CASCADE,
        related_name='guides',
        verbose_name="Categoría",
        null=True,  # Permitir nulos temporalmente
        blank=True  # Permitir dejarlo en blanco en formularios
    )
    
    locations = models.ManyToManyField(
        Location,
        related_name='guides',
        blank=True,
        verbose_name="Ubicaciones relacionadas"
    )
    
    # Autor y control de versiones
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='guides',
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
    
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        verbose_name="Calificación promedio"
    )
    
    rating_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Número de calificaciones"
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
        verbose_name = "Guía pedagógica"
        verbose_name_plural = "Guías pedagógicas"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_media_file(self):
        """Retorna el archivo multimedia principal según el tipo"""
        if self.content_type == 'guide' and self.pdf_file:
            return self.pdf_file
        elif self.content_type == 'worksheet' and self.word_file:
            return self.word_file
        elif self.content_type == 'multimedia':
            if self.video_file:
                return self.video_file
            elif self.audio_file:
                return self.audio_file
            elif self.image_file:
                return self.image_file
        return None
    
    def get_content_type_display_name(self):
        """Retorna el nombre de visualización del tipo de contenido"""
        type_names = {
            'guide': 'Guía Pedagógica',
            'worksheet': 'Ficha Educativa',
            'multimedia': 'Ficha Multimedia',
            'interactive': 'Contenido Interactivo',
        }
        return type_names.get(self.content_type, self.content_type)
    
    def increment_views(self):
        """Incrementa el contador de vistas"""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def increment_downloads(self):
        """Incrementa el contador de descargas"""
        self.downloads_count += 1
        self.save(update_fields=['downloads_count'])
    
    def update_rating(self, new_rating):
        """Actualiza la calificación promedio"""
        total_rating = (self.rating * self.rating_count) + new_rating
        self.rating_count += 1
        self.rating = total_rating / self.rating_count
        self.save(update_fields=['rating', 'rating_count'])

class GuideTag(models.Model):
    """Etiquetas para organizar guías pedagógicas"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Nombre")
    color = models.CharField(max_length=7, default="#6c757d", verbose_name="Color")
    
    class Meta:
        verbose_name = "Etiqueta de guía"
        verbose_name_plural = "Etiquetas de guías"
    
    def __str__(self):
        return self.name

class GuideTagRelation(models.Model):
    """Relación muchos a muchos entre guías y etiquetas"""
    guide = models.ForeignKey(Guide, on_delete=models.CASCADE, related_name='tag_relations')
    tag = models.ForeignKey(GuideTag, on_delete=models.CASCADE, related_name='guide_relations')
    
    class Meta:
        unique_together = ['guide', 'tag']
        verbose_name = "Relación guía-etiqueta"
        verbose_name_plural = "Relaciones guía-etiqueta"
    
    def __str__(self):
        return f"{self.guide.title} - {self.tag.name}"

class GuideRating(models.Model):
    """Calificaciones de usuarios para guías"""
    guide = models.ForeignKey(Guide, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Calificación"
    )
    comment = models.TextField(blank=True, verbose_name="Comentario")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de calificación")
    
    class Meta:
        unique_together = ['guide', 'user']
        verbose_name = "Calificación de guía"
        verbose_name_plural = "Calificaciones de guías"
    
    def __str__(self):
        return f"{self.user.username} - {self.guide.title} ({self.rating}/5)"
