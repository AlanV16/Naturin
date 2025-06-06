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

class PlantType(models.Model):
    """Tipo de planta (árbol, arbusto, hierba, etc.)"""
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Tipo de Planta"
        verbose_name_plural = "Tipos de Planta"

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

class Species(models.Model):
    """Modelo principal para especies (animales y plantas)"""
    CONSERVATION_STATUS_CHOICES = [
        ('NE', 'No Evaluada'),
        ('DD', 'Datos Insuficientes'),
        ('LC', 'Preocupación Menor'),
        ('NT', 'Casi Amenazada'),
        ('VU', 'Vulnerable'),
        ('EN', 'En Peligro'),
        ('CR', 'En Peligro Crítico'),
        ('EW', 'Extinta en Estado Silvestre'),
        ('EX', 'Extinta'),
    ]
    
    HUMAN_DANGER_CHOICES = [
        ('none', 'Ninguno'),
        ('low', 'Bajo'),
        ('medium', 'Medio'),
        ('high', 'Alto'),
        ('extreme', 'Extremo'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Nombre común")
    scientific_name = models.CharField(max_length=200, verbose_name="Nombre científico")
    description = models.TextField(verbose_name="Descripción")
    image = models.ImageField(upload_to='species_images/', blank=True, null=True, verbose_name="Imagen")
    audio = models.FileField(upload_to='species_audio/', blank=True, null=True, verbose_name="Audio")
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='species', verbose_name="Categoría")
    plant_type = models.ForeignKey(PlantType, on_delete=models.SET_NULL, null=True, blank=True, related_name='plants', verbose_name="Tipo de planta")
    
    # Estado de conservación y peligro
    conservation_status = models.CharField(
        max_length=2, 
        choices=CONSERVATION_STATUS_CHOICES, 
        default='NE', 
        verbose_name="Estado de conservación"
    )
    human_danger = models.CharField(
        max_length=10, 
        choices=HUMAN_DANGER_CHOICES, 
        default='none', 
        verbose_name="Peligro para humanos"
    )
    
    # Ubicación
    locations = models.ManyToManyField(Location, related_name='species', blank=True, verbose_name="Ubicaciones")
    
    # Taxonomía adicional
    kingdom = models.CharField(max_length=100, blank=True, verbose_name="Reino")
    phylum = models.CharField(max_length=100, blank=True, verbose_name="Filo")
    class_name = models.CharField(max_length=100, blank=True, verbose_name="Clase")
    order = models.CharField(max_length=100, blank=True, verbose_name="Orden")
    family = models.CharField(max_length=100, blank=True, verbose_name="Familia")
    genus = models.CharField(max_length=100, blank=True, verbose_name="Género")
    
    # Características adicionales
    size = models.CharField(max_length=100, blank=True, verbose_name="Tamaño")
    weight = models.CharField(max_length=100, blank=True, verbose_name="Peso")
    lifespan = models.CharField(max_length=100, blank=True, verbose_name="Esperanza de vida")
    diet = models.CharField(max_length=200, blank=True, verbose_name="Dieta")
    habitat = models.TextField(blank=True, verbose_name="Hábitat")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")
    
    def __str__(self):
        return self.name
    
    def is_endangered(self):
        """Retorna True si la especie está en peligro (VU, EN, CR)"""
        return self.conservation_status in ['VU', 'EN', 'CR']
    
    class Meta:
        verbose_name = "Especie"
        verbose_name_plural = "Especies"
        ordering = ['name']