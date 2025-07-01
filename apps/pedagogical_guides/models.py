from django.db import models
from django.conf import settings

class Guide(models.Model):
    title = models.CharField(max_length=200, verbose_name="Título")
    description = models.TextField(verbose_name="Descripción")
    pdf = models.FileField(upload_to='guides/', verbose_name="Archivo PDF")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Autor")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")
    is_public = models.BooleanField(default=True, verbose_name="Público")

    class Meta:
        verbose_name = "Guía pedagógica"
        verbose_name_plural = "Guías pedagógicas"
        ordering = ['-created_at']

    def __str__(self):
        return self.title
