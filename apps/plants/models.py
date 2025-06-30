from django.db import models
from apps.common.models import SpeciesBase

class PlantType(models.Model):
    """Tipo de planta (árbol, arbusto, hierba, etc.)"""
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tipo de Planta"
        verbose_name_plural = "Tipos de Planta"


class Plant(SpeciesBase):
    """Modelo de planta específico"""
    plant_type = models.ForeignKey(
        PlantType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plants',
        verbose_name="Tipo de planta"
    )

    conservation_status = models.CharField(
        max_length=2,
        choices=[
            ('NE','No Evaluada'),
            ('DD', 'Datos Insuficientes'),
            ('LC', 'Preocupación Menor'),
            ('NT', 'Casi Amenazada'),
            ('VU', 'Vulnerable'),
            ('EN', 'En Peligro'),
            ('CR', 'En Peligro Crítico'),
            ('EW', 'Extinta en Estado Silvestre'),
            ('EX', 'Extinta'),
        ],
        default='NE',
        verbose_name="Estado de conservación"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Planta"
        verbose_name_plural = "Plantas"
        ordering = ['name']
