from apps.accounts.models import User
from django.db import models
from django.urls import reverse

class SpeciesCategory(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Categorías de especies"
    
    def __str__(self):
        return self.name

class Species(models.Model):
    CONSERVATION_STATUS = (
        ('LC', 'Preocupación menor'),
        ('NT', 'Casi amenazada'),
        ('VU', 'Vulnerable'),
        ('EN', 'En peligro'),
        ('CR', 'En peligro crítico'),
    )
    
    name = models.CharField(max_length=100)
    scientific_name = models.CharField(max_length=100)
    category = models.ForeignKey(SpeciesCategory, on_delete=models.PROTECT)
    description = models.TextField()
    habitat = models.TextField()
    diet = models.TextField()
    conservation_status = models.CharField(max_length=2, choices=CONSERVATION_STATUS)
    fun_fact = models.TextField(blank=True)
    is_local = models.BooleanField(default=True)
    region = models.CharField(max_length=100, blank=True)
    slug = models.SlugField(unique=True)
    
    class Meta:
        verbose_name_plural = "Especies"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.scientific_name})"
    
    def get_absolute_url(self):
        return reverse('species_detail', kwargs={'slug': self.slug})

class SpeciesImage(models.Model):
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='species/')
    caption = models.CharField(max_length=200, blank=True)
    is_featured = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Imagen de {self.species.name}"

class SpeciesSound(models.Model):
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name='sounds')
    sound = models.FileField(upload_to='sounds/')
    description = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"Sonido de {self.species.name}"

class EducationalResource(models.Model):
    RESOURCE_TYPES = (
        ('video', 'Video'),
        ('pdf', 'PDF'),
        ('image', 'Imagen'),
        ('audio', 'Audio'),
        ('link', 'Enlace'),
    )
    
    title = models.CharField(max_length=200)
    resource_type = models.CharField(max_length=10, choices=RESOURCE_TYPES)
    file = models.FileField(upload_to='resources/', blank=True, null=True)
    url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    species = models.ManyToManyField(Species, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title