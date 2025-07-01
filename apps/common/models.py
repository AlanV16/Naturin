from django.db import models

class Category(models.Model):
    """Categoría general de la especie (aves, mamíferos, insectos, peces, etc.)"""
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"


class Location(models.Model):
    """Ubicación geográfica de la especie"""
    name = models.CharField(max_length=200, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    latitude = models.FloatField(blank=True, null=True, verbose_name="Latitud")
    longitude = models.FloatField(blank=True, null=True, verbose_name="Longitud")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Ubicación"
        verbose_name_plural = "Ubicaciones"


class SpeciesBase(models.Model):
    """Modelo base abstracto para especies (plantas y animales)"""

    name = models.CharField(max_length=200, verbose_name="Nombre común")
    scientific_name = models.CharField(max_length=200, verbose_name="Nombre científico")
    description = models.TextField(verbose_name="Descripción")
    image = models.ImageField(upload_to='species_images/', blank=True, null=True, verbose_name="Imagen")
    audio = models.FileField(upload_to='species_audio/', blank=True, null=True, verbose_name="Audio")

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="%(class)s_category",
        verbose_name="Categoría"
    )

    locations = models.ManyToManyField(
        Location,
        related_name="%(class)s_locations",
        blank=True,
        verbose_name="Ubicaciones"
    )

    # Taxonomía
    kingdom = models.CharField(max_length=100, blank=True, verbose_name="Reino")
    phylum = models.CharField(max_length=100, blank=True, verbose_name="Filo")
    class_name = models.CharField(max_length=100, blank=True, verbose_name="Clase")
    order = models.CharField(max_length=100, blank=True, verbose_name="Orden")
    family = models.CharField(max_length=100, blank=True, verbose_name="Familia")
    genus = models.CharField(max_length=100, blank=True, verbose_name="Género")

    # Características generales
    size = models.CharField(max_length=100, blank=True, verbose_name="Tamaño")
    weight = models.CharField(max_length=100, blank=True, verbose_name="Peso")
    lifespan = models.CharField(max_length=100, blank=True, verbose_name="Esperanza de vida")
    habitat = models.TextField(blank=True, verbose_name="Hábitat")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        abstract = True

