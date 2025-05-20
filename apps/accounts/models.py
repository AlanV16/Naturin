from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        (1, 'Estudiante'),
        (2, 'Docente'),
        (3, 'Padre/Madre'),
        (4, 'Administrador'),
    )
    
    user_type = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES, default=1)
    birth_date = models.DateField(null=True, blank=True)
    school = models.CharField(max_length=100, blank=True)
    grade = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"

class ParentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')
    children = models.ManyToManyField(User, related_name='parents', blank=True)
    
    def __str__(self):
        return f"Perfil de padre/madre: {self.user}"

class StudentProgress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='progress')
    points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    badges = models.ManyToManyField('gamification.Badge', blank=True)
    last_active = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Progreso de {self.user}"