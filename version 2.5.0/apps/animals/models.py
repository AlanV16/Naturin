from django.db import models
from apps.common.models import SpeciesBase

class Animal(SpeciesBase):
    """Modelo de animal específico"""

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

    diet = models.CharField(max_length=200, blank=True, verbose_name="Dieta")

    def is_endangered(self):
        return self.conservation_status in ['VU', 'EN', 'CR']

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Animal"
        verbose_name_plural = "Animales"
        ordering = ['name']
