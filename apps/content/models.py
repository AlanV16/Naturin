from django.db import models

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
