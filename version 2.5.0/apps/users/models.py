from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import random
import string

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        (1, 'Estudiante'),
        (2, 'Docente'),
        (3, 'Padre/Madre'),
        (4, 'Administrador'),
    )

    email = models.EmailField(unique=True)
    user_type = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES, default=1)
    birth_date = models.DateField(null=True, blank=True)
    school = models.CharField(max_length=100, blank=True)
    grade = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    # Campos para verificación de email
    is_email_verified = models.BooleanField(default=False)
    email_verification_code = models.CharField(max_length=6, blank=True)
    email_verification_created = models.DateTimeField(null=True, blank=True)
    
    # Campos para reset de contraseña
    password_reset_code = models.CharField(max_length=6, blank=True)
    password_reset_created = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"

    def generate_verification_code(self):
        """Genera un código de verificación de 6 dígitos"""
        self.email_verification_code = ''.join(random.choices(string.digits, k=6))
        self.email_verification_created = timezone.now()
        self.save()
        return self.email_verification_code

    def is_verification_code_valid(self, code):
        """Verifica si el código es válido y no ha expirado"""
        if not self.email_verification_code or not self.email_verification_created:
            return False
        
        # Verificar si el código coincide
        if self.email_verification_code != code:
            return False
        
        # Verificar si no ha expirado (15 minutos)
        time_diff = timezone.now() - self.email_verification_created
        if time_diff.total_seconds() > 900:  # 15 minutos
            return False
        
        return True

    def verify_email(self):
        """Marca el email como verificado"""
        self.is_email_verified = True
        self.email_verification_code = ''
        self.email_verification_created = None
        self.save()

    def generate_password_reset_code(self):
        """Genera un código de reset de contraseña de 6 dígitos"""
        self.password_reset_code = ''.join(random.choices(string.digits, k=6))
        self.password_reset_created = timezone.now()
        self.save()
        return self.password_reset_code

    def is_password_reset_code_valid(self, code):
        """Verifica si el código de reset es válido y no ha expirado"""
        if not self.password_reset_code or not self.password_reset_created:
            return False
        
        # Verificar si el código coincide
        if self.password_reset_code != code:
            return False
        
        # Verificar si no ha expirado (15 minutos)
        time_diff = timezone.now() - self.password_reset_created
        if time_diff.total_seconds() > 900:  # 15 minutos
            return False
        
        return True

    def clear_password_reset_code(self):
        """Limpia el código de reset de contraseña"""
        self.password_reset_code = ''
        self.password_reset_created = None
        self.save()



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
