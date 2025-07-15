from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.db.models import Q
import random
import string

class User(AbstractUser):
    USER_TYPE_CHOICES = [
        (1, 'Estudiante'),
        (2, 'Docente'),
        (3, 'Padre'),
        (4, 'Experto'),
        (5, 'Administrador'),
    ]
    
    user_type = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES, default=1)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    
    # Campos específicos para estudiantes
    school = models.CharField(max_length=200, blank=True)
    grade = models.CharField(max_length=20, blank=True)
    
    # Campos específicos para expertos
    expertise_areas = models.TextField(
        blank=True,
        help_text="Áreas de especialización del experto (separadas por comas)"
    )
    professional_title = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Título profesional"
    )
    institution = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Institución"
    )
    years_experience = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Años de experiencia"
    )
    
    # Campos de verificación
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    

    
    def is_student(self):
        return self.user_type == 1
    
    def is_teacher(self):
        return self.user_type == 2
    
    def is_parent(self):
        return self.user_type == 3
    def is_expert(self):
        return self.user_type == 4
    
    def is_admin(self):
        return self.user_type == 5

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
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='book')
    color_class = models.CharField(max_length=50, default='primary')
    created_at = models.DateTimeField(auto_now_add=True)
    
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
    grade = models.CharField(max_length=50, blank=True)  # Campo grade que falta

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    class Meta:
        ordering = ['-created_at']   
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
    ASSIGNMENT_STATUS = [
        ('draft', 'Borrador'),
        ('published', 'Publicado'), 
        ('closed', 'Cerrado'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructions = models.TextField(blank=True)
    due_date = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=ASSIGNMENT_STATUS, default='published')
    max_points = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    allow_late_submission = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='assignments/', null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.course.name}"
    
    def is_overdue(self):
        return timezone.now() > self.due_date
    
    def days_until_due(self):
        if self.is_overdue():
            return 0
        delta = self.due_date - timezone.now()
        return delta.days
    
    def get_attachment_icon(self):
        if self.attachment:
            ext = self.attachment.name.split('.')[-1].lower()
            if ext in ['pdf']:
                return 'bi-file-pdf'
            elif ext in ['doc', 'docx']:
                return 'bi-file-word'
            elif ext in ['jpg', 'jpeg', 'png', 'gif']:
                return 'bi-file-image'
        return 'bi-file-earmark'

class AssignmentSubmission(models.Model):
    SUBMISSION_STATUS = [
        ('submitted', 'Entregado'),
        ('graded', 'Calificado'),
        ('returned', 'Devuelto'),
    ]
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    submission_text = models.TextField(blank=True)
    attachment = models.FileField(upload_to='submissions/', null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=SUBMISSION_STATUS, default='submitted')
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    is_late = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['assignment', 'student']
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"

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



class Conversation(models.Model):
    """Modelo para conversaciones entre usuarios"""
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_group = models.BooleanField(default=False)
    group_name = models.CharField(max_length=100, blank=True)
    group_description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_conversations', null=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.is_group:
            return self.group_name or f"Grupo {self.id}"
        participants = self.participants.all()[:2]
        return f"Conversación entre {' y '.join([p.username for p in participants])}"
    
    def get_last_message(self):
        return self.messages.order_by('-timestamp').first()
    
    def get_other_participant(self, current_user):
        """Obtener el otro participante en una conversación de 2 personas"""
        if not self.is_group:
            return self.participants.exclude(id=current_user.id).first()
        return None
    
    def mark_as_read(self, user):
        """Marcar todos los mensajes como leídos para un usuario"""
        self.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    # Cambiar esta línea - usar 'self' para la referencia al mismo modelo:
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Campos adicionales para funcionalidad avanzada
    message_type = models.CharField(max_length=20, choices=[
        ('text', 'Texto'),
        ('image', 'Imagen'),
        ('file', 'Archivo'),
        ('system', 'Sistema'),
    ], default='text')
    
    file_attachment = models.FileField(upload_to='message_attachments/', null=True, blank=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
            models.Index(fields=['sender']),
            models.Index(fields=['is_read']),
        ]
    
    def __str__(self):
        return f'{self.sender.username}: {self.content[:50]}...'
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])

class MessageReadStatus(models.Model):
    """Modelo para tracking de lectura de mensajes en grupos"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_status')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('message', 'user')

class Contact(models.Model):
    """Modelo para contactos/lista de amigos"""
    CONTACT_STATUS = [
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptado'),
        ('blocked', 'Bloqueado'),
        ('rejected', 'Rechazado'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    contact = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contact_of')
    status = models.CharField(max_length=10, choices=CONTACT_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    nickname = models.CharField(max_length=50, blank=True)  # Nombre personalizado para el contacto
    
    class Meta:
        unique_together = ('user', 'contact')
    
    def __str__(self):
        return f"{self.user.username} -> {self.contact.username} ({self.status})"

class ContactRequest(models.Model):
    """Modelo para solicitudes de contacto"""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptado'),
        ('rejected', 'Rechazado'),
    ]
    
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_contact_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_contact_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    message = models.TextField(blank=True, help_text="Mensaje opcional con la solicitud")
    
    class Meta:
        unique_together = ('from_user', 'to_user')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Solicitud de {self.from_user.username} a {self.to_user.username} ({self.status})"

class CalendarEvent(models.Model):
    EVENT_TYPES = [
        ('class', 'Clase'),
        ('assignment', 'Tarea'),
        ('exam', 'Examen'),
        ('meeting', 'Reunión'),
        ('workshop', 'Taller'),
        ('deadline', 'Fecha límite'),
        ('reminder', 'Recordatorio'),
        ('conference', 'Conferencia'),
        ('project', 'Proyecto'),
        ('holiday', 'Feriado'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calendar_events')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_calendar_events')
    course = models.ForeignKey('Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='calendar_events')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='class')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    participants = models.ManyToManyField(User, related_name='participated_events', blank=True)

    def __str__(self):
        return f"{self.title} ({self.start_date} - {self.end_date})"
    
    def is_today(self):
        """Verificar si el evento es hoy"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.start_date.date() == today
    
    def is_upcoming(self):
        """Verificar si el evento es próximo (después de hoy)"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.start_date.date() > today
    
    def get_color_class(self):
        """Obtener clase CSS según el tipo de evento"""
        color_map = {
            'class': 'event-class',
            'assignment': 'event-assignment', 
            'exam': 'event-exam',
            'meeting': 'event-meeting',
            'workshop': 'event-workshop',
            'deadline': 'event-deadline',
            'reminder': 'event-reminder',
            'conference': 'event-conference',
            'project': 'event-project',
            'holiday': 'event-holiday',
        }
        return color_map.get(self.event_type, 'event-default')
    
    def get_icon(self):
        """Obtener icono según el tipo de evento"""
        icon_map = {
            'class': 'book',
            'assignment': 'clipboard-check',
            'exam': 'pencil-square',
            'meeting': 'people',
            'workshop': 'tools',
            'deadline': 'clock',
            'reminder': 'bell',
            'conference': 'camera-video',
            'project': 'folder',
            'holiday': 'star',
        }
        return icon_map.get(self.event_type, 'calendar-event')

class Material(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='course_materials/', null=True, blank=True)
    url = models.URLField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} - {self.course.name}"
    
    def get_file_icon(self):
        if self.url:
            return 'bi-link'
        
        if self.file:
            ext = self.file.name.split('.')[-1].lower()
            if ext in ['pdf']:
                return 'bi-file-pdf'
            elif ext in ['doc', 'docx']:
                return 'bi-file-word'
            elif ext in ['xls', 'xlsx']:
                return 'bi-file-excel'
            elif ext in ['ppt', 'pptx']:
                return 'bi-file-ppt'
            elif ext in ['jpg', 'jpeg', 'png', 'gif', 'svg']:
                return 'bi-file-image'
            elif ext in ['mp4', 'avi', 'mov', 'mkv']:
                return 'bi-file-play'
            elif ext in ['zip', 'rar', '7z']:
                return 'bi-file-zip'
            elif ext in ['txt']:
                return 'bi-file-text'
        
        return 'bi-file-earmark'

