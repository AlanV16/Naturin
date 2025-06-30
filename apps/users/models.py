from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        (1, 'Estudiante'),
        (2, 'Docente'),
        (3, 'Padre/Madre'),
        (4, 'Administrador'),
        (5, 'Experto'),
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
    badges = models.ManyToManyField('gamification.Badge', related_name='progress_badges', blank=True)  # Relación directa
    last_active = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Progreso de {self.user}"

class Class(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 2})
    name = models.CharField(max_length=100)
    grade = models.CharField(max_length=20, choices=[('1° de Secundaria', '1° de Secundaria'), ('2° de Secundaria', '2° de Secundaria')])
    section = models.CharField(max_length=20, choices=[('Sección A', 'Sección A'), ('Sección B', 'Sección B'), ('Sección C', 'Sección C'), ('Sección D', 'Sección D')])
    description = models.TextField(blank=True)
    access_code = models.CharField(max_length=8, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.grade} - {self.section})"

class StudentClass(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 1})
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'class_id')

    def __str__(self):
        return f"{self.student} en {self.class_id}"