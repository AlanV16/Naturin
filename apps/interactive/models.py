from apps.accounts.models import User
from django.db import models
from apps.content.models import Especie

class InteractiveMap(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='maps/')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

class MapPoint(models.Model):
    interactive_map = models.ForeignKey(InteractiveMap, on_delete=models.CASCADE, related_name='points')
    title = models.CharField(max_length=100)
    description = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    species = models.ManyToManyField(Especie, blank=True)
    image = models.ImageField(upload_to='map_points/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.title} - {self.interactive_map}"

class VirtualTour(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    url = models.URLField()
    thumbnail = models.ImageField(upload_to='virtual_tours/')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title