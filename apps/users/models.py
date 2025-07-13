from django.contrib.auth.models import AbstractUser, User
from django.db import models
from django.utils import timezone
from django.db.models import Q
import random
import string

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
    last_active = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Progreso de {self.user}"


class Subject(models.Model):
    """Modelo para las materias"""
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='book')
    color_class = models.CharField(max_length=20, default='math')
    
    def __str__(self):
        return self.name

class Course(models.Model):
    """Modelo para los cursos"""
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('completed', 'Completado'),
        ('archived', 'Archivado'),
    ]
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='taught_courses')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def students_count(self):
        """Contar estudiantes inscritos"""
        try:
            return self.enrollment_set.count()
        except:
            return 0
    
    def assignments_count(self):
        """Contar tareas del curso"""
        try:
            return self.assignments.count()
        except:
            return 0

class Enrollment(models.Model):
    """Modelo para la inscripción de estudiantes en cursos"""
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    progress = models.FloatField(default=0.0)
    
    class Meta:
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.name}"

class Assignment(models.Model):
    """Modelo para las tareas"""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('submitted', 'Entregada'),
        ('graded', 'Calificada'),
        ('late', 'Tardía'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    points = models.IntegerField(default=100)
    
    def __str__(self):
        return f"{self.title} - {self.course.name}"

class AssignmentSubmission(models.Model):
    """Modelo para las entregas de tareas"""
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    file = models.FileField(upload_to='submissions/', blank=True, null=True)
    grade = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['assignment', 'student']
    
    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"
    
    @property
    def status(self):
        if self.grade is not None:
            return 'graded'
        elif self.submitted_at > self.assignment.due_date:
            return 'late'
        else:
            return 'submitted'

class Achievement(models.Model):
    """Modelo para los logros"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='star-fill')
    points = models.IntegerField(default=10)
    
    def __str__(self):
        return self.name

class StudentAchievement(models.Model):
    """Modelo para los logros obtenidos por estudiantes"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'achievement']
    
    def __str__(self):
        return f"{self.student.username} - {self.achievement.name}"

class Event(models.Model):
    """Modelo para eventos y clases programadas"""
    EVENT_TYPES = [
        ('class', 'Clase'),
        ('exam', 'Examen'),
        ('meeting', 'Reunión'),
        ('workshop', 'Taller'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='class')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.course.name}"

class Notification(models.Model):
    """Modelo para notificaciones"""
    TYPE_CHOICES = [
        ('assignment', 'Tarea'),
        ('grade', 'Calificación'),
        ('announcement', 'Anuncio'),
        ('achievement', 'Logro'),
        ('reminder', 'Recordatorio'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class Message(models.Model):
    """Modelo para mensajes entre usuarios"""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_received_messages')
    subject = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    parent_message = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"De {self.sender.username} a {self.recipient.username}: {self.subject}"
    
    def get_conversation_messages(self):
        """Obtener todos los mensajes de la conversación"""
        if self.parent_message:
            # Si es una respuesta, obtener el mensaje padre y todas sus respuestas
            parent = self.parent_message
            return Message.objects.filter(
                Q(id=parent.id) | Q(parent_message=parent)
            ).order_by('created_at')
        else:
            # Si es el mensaje principal, obtener él y todas sus respuestas
            return Message.objects.filter(
                Q(id=self.id) | Q(parent_message=self)
            ).order_by('created_at')


class Conversation(models.Model):
    """Modelo para conversaciones entre usuarios"""
    participants = models.ManyToManyField(User, related_name='conversations')
    name = models.CharField(max_length=200, blank=True, null=True)  # Nombre opcional para la conversación
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.name:
            return self.name
        participants_names = ", ".join([user.username for user in self.participants.all()])
        return f"Conversación: {participants_names}"
    
    def get_latest_message(self):
        """Obtener el último mensaje de la conversación"""
        return self.conversation_messages.order_by('-created_at').first()
    
    def mark_as_read_for_user(self, user):
        """Marcar todos los mensajes como leídos para un usuario específico"""
        self.conversation_messages.filter(
            sender__in=self.participants.exclude(id=user.id),
            is_read=False
        ).update(is_read=True)


class ConversationMessage(models.Model):
    """Modelo para mensajes dentro de conversaciones"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='conversation_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}..."