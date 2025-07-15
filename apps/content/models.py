from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

# Create your models here.

class Place(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    template = models.CharField(max_length=200, help_text='Ruta de la plantilla HTML específica para este lugar')
    image = models.ImageField(upload_to='places/', blank=True, null=True)
    map_url = models.URLField(blank=True, null=True, help_text='URL de Google Maps para este lugar')
    # Puedes agregar más campos según lo que necesites (galería, ubicación, etc)

    def __str__(self):
        return self.name


class ContentCategory(models.Model):
    """Categorías de contenido educativo"""
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    icon = models.CharField(max_length=50, default='folder', verbose_name="Icono")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    class Meta:
        verbose_name = "Categoría de Contenido"
        verbose_name_plural = "Categorías de Contenido"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class EducationalSheet(models.Model):
    """Fichas educativas del sistema"""
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('pending_review', 'Pendiente de Revisión'),
        ('in_review', 'En Revisión'),
        ('approved', 'Aprobada'),
        ('rejected', 'Rechazada'),
        ('published', 'Publicada'),
        ('archived', 'Archivada'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('beginner', 'Principiante'),
        ('intermediate', 'Intermedio'),
        ('advanced', 'Avanzado'),
    ]
    
    SHEET_TYPE_CHOICES = [
        ('flora', 'Flora'),
        ('fauna', 'Fauna'),
        ('ecosystem', 'Lugar/Ecosistema'),
    ]
    
    # Información básica
    title = models.CharField(max_length=200, verbose_name="Título")
    description = models.TextField(verbose_name="Descripción")
    content = models.TextField(verbose_name="Contenido")
    
    # Tipo de ficha
    sheet_type = models.CharField(
        max_length=20,
        choices=SHEET_TYPE_CHOICES,
        default='flora',
        verbose_name="Tipo de Ficha"
    )
    
    # Metadatos
    category = models.ForeignKey(
        ContentCategory,
        on_delete=models.CASCADE,
        related_name='sheets',
        verbose_name="Categoría"
    )
    tags = models.CharField(
        max_length=500,
        blank=True,
        help_text="Etiquetas separadas por comas"
    )
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='beginner',
        verbose_name="Dificultad"
    )
    
    # Recursos multimedia
    featured_image = models.ImageField(
        upload_to='educational_sheets/images/',
        blank=True,
        null=True,
        verbose_name="Imagen destacada"
    )
    attachments = models.FileField(
        upload_to='educational_sheets/attachments/',
        blank=True,
        null=True,
        verbose_name="Archivos adjuntos"
    )
    
    # Gestión de estado
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Estado"
    )
    
    # Usuarios involucrados
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authored_sheets',
        verbose_name="Autor"
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_sheets',
        verbose_name="Revisor"
    )
    
    # Campos de revisión
    review_notes = models.TextField(
        blank=True,
        verbose_name="Notas de revisión"
    )
    review_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de revisión"
    )
    
    # Campos de publicación
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de publicación"
    )
    
    # Estadísticas
    views_count = models.PositiveIntegerField(default=0, verbose_name="Visualizaciones")
    downloads_count = models.PositiveIntegerField(default=0, verbose_name="Descargas")
    
    # Metadatos temporales
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado")
    
    class Meta:
        verbose_name = "Ficha Educativa"
        verbose_name_plural = "Fichas Educativas"
        ordering = ['-created_at']
        permissions = [
            ("can_review_sheets", "Puede revisar fichas"),
            ("can_publish_sheets", "Puede publicar fichas"),
            ("can_moderate_content", "Puede moderar contenido"),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    def can_be_reviewed(self):
        return self.status in ['pending_review', 'in_review']
    
    def can_be_published(self):
        return self.status == 'approved'
    
    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]


class SheetRevisionHistory(models.Model):
    """Historial de revisiones de fichas educativas"""
    
    ACTION_CHOICES = [
        ('created', 'Creada'),
        ('submitted', 'Enviada para revisión'),
        ('reviewed', 'Revisada'),
        ('approved', 'Aprobada'),
        ('rejected', 'Rechazada'),
        ('published', 'Publicada'),
        ('edited', 'Editada'),
        ('archived', 'Archivada'),
    ]
    
    sheet = models.ForeignKey(
        EducationalSheet,
        on_delete=models.CASCADE,
        related_name='revision_history',
        verbose_name="Ficha"
    )
    
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name="Acción"
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Usuario"
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name="Notas/Comentarios"
    )
    
    # Campos de versión
    version_number = models.PositiveIntegerField(default=1, verbose_name="Número de versión")
    changes_summary = models.TextField(
        blank=True,
        verbose_name="Resumen de cambios"
    )
    
    # Snapshot de datos importantes
    status_before = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Estado anterior"
    )
    status_after = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Estado posterior"
    )
    
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y hora")
    
    class Meta:
        verbose_name = "Historial de Revisión"
        verbose_name_plural = "Historial de Revisiones"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.sheet.title} - {self.get_action_display()} por {self.user.username}"


class StudentContent(models.Model):
    """Contenido creado por estudiantes"""
    
    CONTENT_TYPE_CHOICES = [
        ('comment', 'Comentario'),
        ('question', 'Pregunta'),
        ('answer', 'Respuesta'),
        ('project', 'Proyecto'),
        ('drawing', 'Dibujo'),
        ('story', 'Historia'),
    ]
    
    MODERATION_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
        ('flagged', 'Marcado'),
    ]
    
    # Información básica
    title = models.CharField(max_length=200, verbose_name="Título")
    content = models.TextField(verbose_name="Contenido")
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        verbose_name="Tipo de contenido"
    )
    
    # Autor
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='student_content',
        verbose_name="Autor"
    )
    
    # Relación con ficha educativa
    related_sheet = models.ForeignKey(
        EducationalSheet,
        on_delete=models.CASCADE,
        related_name='student_content',
        null=True,
        blank=True,
        verbose_name="Ficha relacionada"
    )
    
    # Moderación
    moderation_status = models.CharField(
        max_length=20,
        choices=MODERATION_STATUS_CHOICES,
        default='pending',
        verbose_name="Estado de moderación"
    )
    
    moderator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_content',
        verbose_name="Moderador"
    )
    
    moderation_notes = models.TextField(
        blank=True,
        verbose_name="Notas de moderación"
    )
    
    moderation_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de moderación"
    )
    
    # Archivos adjuntos
    attachment = models.FileField(
        upload_to='student_content/',
        blank=True,
        null=True,
        verbose_name="Archivo adjunto"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado")
    
    class Meta:
        verbose_name = "Contenido de Estudiante"
        verbose_name_plural = "Contenido de Estudiantes"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.author.username}"
