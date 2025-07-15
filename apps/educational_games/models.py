from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()

# ============================================================================
# MODELOS BASE PARA ACTIVIDADES EDUCATIVAS
# ============================================================================

class ActivityType(models.Model):
    """Tipos de actividades educativas disponibles"""
    ACTIVITY_TYPES = [
        ('assignment', 'Tarea'),
        ('reading', 'Lectura'),
        ('test', 'Test'),
        ('game', 'Juego'),
        ('worksheet', 'Ficha Educativa'),
        ('multimedia', 'Ficha Multimedia'),
    ]
    
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, choices=ACTIVITY_TYPES, verbose_name="Nombre del Tipo")
    description = models.TextField(blank=True, verbose_name="Descripción")
    icon = models.CharField(max_length=50, default="bi-file-text", verbose_name="Icono")
    color = models.CharField(max_length=20, default="primary", verbose_name="Color")
    
    def __str__(self):
        return self.get_name_display()
    
    class Meta:
        verbose_name = "Tipo de Actividad"
        verbose_name_plural = "Tipos de Actividades"

class BaseActivity(models.Model):
    """Modelo base para todas las actividades educativas"""
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200, verbose_name="Título")
    description = models.TextField(verbose_name="Descripción")
    instructions = models.TextField(verbose_name="Instrucciones")
    points = models.IntegerField(
        default=100,
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
        verbose_name="Puntuación"
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name="Autor"
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name="¿Es pública?",
        help_text="Si está marcado, otros docentes pueden usar esta actividad como plantilla"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

# ============================================================================
# MODELOS DE TAREAS
# ============================================================================

class Assignment(BaseActivity):
    """Tareas asignadas por docentes"""
    due_date = models.DateTimeField(verbose_name="Fecha de Entrega")
    time_limit = models.IntegerField(
        default=0,
        verbose_name="Tiempo Límite (minutos)",
        help_text="0 = sin límite de tiempo"
    )
    allow_late_submission = models.BooleanField(
        default=False,
        verbose_name="Permitir entrega tardía"
    )
    max_attempts = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="Máximo de intentos"
    )
    
    # Corregir related_name para evitar conflictos
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='created_assignments',
        verbose_name="Autor"
    )
    
    class Meta:
        verbose_name = "Tarea"
        verbose_name_plural = "Tareas"

class AssignmentSubmission(models.Model):
    """Entregas de tareas por estudiantes"""
    id = models.AutoField(primary_key=True)
    assignment = models.ForeignKey(
        Assignment, 
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name="Tarea"
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assignment_submissions',
        verbose_name="Estudiante"
    )
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Entrega")
    content = models.TextField(blank=True, verbose_name="Contenido")
    file = models.FileField(
        upload_to='assignments/submissions/',
        blank=True,
        null=True,
        verbose_name="Archivo"
    )
    grade = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name="Calificación"
    )
    feedback = models.TextField(blank=True, verbose_name="Comentarios")
    is_late = models.BooleanField(default=False, verbose_name="Entrega tardía")
    attempt_number = models.IntegerField(default=1, verbose_name="Número de intento")
    
    class Meta:
        verbose_name = "Entrega de Tarea"
        verbose_name_plural = "Entregas de Tareas"
        unique_together = ['assignment', 'student', 'attempt_number']
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.assignment.title}"

class CompetencyEvaluation(models.Model):
    """Evaluación por competencias del diseño curricular nacional"""
    COMPETENCIES = [
        ('comunicacion', 'Comunicación'),
        ('pensamiento_critico', 'Pensamiento Crítico'),
        ('resolucion_problemas', 'Resolución de Problemas'),
        ('creatividad', 'Creatividad'),
        ('colaboracion', 'Colaboración'),
        ('autonomia', 'Autonomía'),
        ('responsabilidad', 'Responsabilidad'),
        ('empatia', 'Empatía'),
    ]
    
    id = models.AutoField(primary_key=True)
    submission = models.ForeignKey(
        AssignmentSubmission,
        on_delete=models.CASCADE,
        related_name='competency_evaluations',
        verbose_name="Entrega"
    )
    competency = models.CharField(max_length=50, choices=COMPETENCIES, verbose_name="Competencia")
    score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name="Puntuación"
    )
    comments = models.TextField(blank=True, verbose_name="Comentarios")
    evaluated_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Evaluación")
    
    class Meta:
        verbose_name = "Evaluación por Competencia"
        verbose_name_plural = "Evaluaciones por Competencias"
        unique_together = ['submission', 'competency']
    
    def __str__(self):
        return f"{self.submission} - {self.get_competency_display()}"

# ============================================================================
# MODELOS DE LECTURAS
# ============================================================================

class Reading(BaseActivity):
    """Lecturas educativas"""
    content = models.TextField(verbose_name="Contenido de la Lectura")
    estimated_time = models.IntegerField(
        default=10,
        verbose_name="Tiempo Estimado (minutos)"
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('easy', 'Fácil'),
            ('medium', 'Medio'),
            ('hard', 'Difícil'),
        ],
        default='medium',
        verbose_name="Nivel de Dificultad"
    )
    
    # Corregir related_name para evitar conflictos
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='created_readings',
        verbose_name="Autor"
    )
    
    class Meta:
        verbose_name = "Lectura"
        verbose_name_plural = "Lecturas"

class ReadingProgress(models.Model):
    """Progreso de estudiantes en lecturas"""
    id = models.AutoField(primary_key=True)
    reading = models.ForeignKey(
        Reading,
        on_delete=models.CASCADE,
        related_name='progress',
        verbose_name="Lectura"
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reading_progress',
        verbose_name="Estudiante"
    )
    completed = models.BooleanField(default=False, verbose_name="Completada")
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de Completado")
    time_spent = models.IntegerField(default=0, verbose_name="Tiempo Dedicado (segundos)")
    
    class Meta:
        verbose_name = "Progreso de Lectura"
        verbose_name_plural = "Progresos de Lecturas"
        unique_together = ['reading', 'student']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.reading.title}"

# ============================================================================
# MODELOS DE TESTS
# ============================================================================

class Test(BaseActivity):
    """Tests educativos"""
    time_limit = models.IntegerField(
        default=30,
        verbose_name="Tiempo Límite (minutos)"
    )
    passing_score = models.IntegerField(
        default=60,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Puntuación Mínima (%)"
    )
    shuffle_questions = models.BooleanField(
        default=False,
        verbose_name="Mezclar preguntas"
    )
    show_results_immediately = models.BooleanField(
        default=True,
        verbose_name="Mostrar resultados inmediatamente"
    )
    allow_multiple_attempts = models.BooleanField(
        default=False,
        verbose_name="Permitir múltiples intentos"
    )
    
    # Corregir related_name para evitar conflictos
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='created_tests',
        verbose_name="Autor"
    )
    
    class Meta:
        verbose_name = "Test"
        verbose_name_plural = "Tests"

class Question(models.Model):
    """Preguntas de tests"""
    QUESTION_TYPES = [
        ('multiple_choice', 'Opción Múltiple'),
        ('true_false', 'Verdadero/Falso'),
        ('short_answer', 'Respuesta Corta'),
        ('matching', 'Relacionar'),
    ]
    
    id = models.AutoField(primary_key=True)
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="Test"
    )
    question_text = models.TextField(verbose_name="Pregunta")
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        default='multiple_choice',
        verbose_name="Tipo de Pregunta"
    )
    points = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name="Puntos"
    )
    order = models.IntegerField(default=1, verbose_name="Orden")
    
    class Meta:
        verbose_name = "Pregunta"
        verbose_name_plural = "Preguntas"
        ordering = ['test', 'order']
    
    def __str__(self):
        return f"{self.test.title} - Pregunta {self.order}"

class QuestionOption(models.Model):
    """Opciones para preguntas de opción múltiple"""
    id = models.AutoField(primary_key=True)
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name="Pregunta"
    )
    option_text = models.CharField(max_length=500, verbose_name="Texto de la Opción")
    is_correct = models.BooleanField(default=False, verbose_name="¿Es correcta?")
    order = models.IntegerField(default=1, verbose_name="Orden")
    
    class Meta:
        verbose_name = "Opción de Pregunta"
        verbose_name_plural = "Opciones de Preguntas"
        ordering = ['question', 'order']
    
    def __str__(self):
        return f"{self.question} - Opción {self.order}"

class TestAttempt(models.Model):
    """Intentos de estudiantes en tests"""
    id = models.AutoField(primary_key=True)
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name="Test"
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='test_attempts',
        verbose_name="Estudiante"
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Iniciado")
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name="Completado")
    score = models.IntegerField(default=0, verbose_name="Puntuación")
    max_score = models.IntegerField(default=0, verbose_name="Puntuación Máxima")
    time_spent = models.IntegerField(default=0, verbose_name="Tiempo Empleado (segundos)")
    is_completed = models.BooleanField(default=False, verbose_name="Completado")
    
    class Meta:
        verbose_name = "Intento de Test"
        verbose_name_plural = "Intentos de Tests"
        unique_together = ['test', 'student']
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.test.title}"

class TestAnswer(models.Model):
    """Respuestas de estudiantes en tests"""
    id = models.AutoField(primary_key=True)
    attempt = models.ForeignKey(
        TestAttempt,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name="Intento"
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        verbose_name="Pregunta"
    )
    selected_option = models.ForeignKey(
        QuestionOption,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Opción Seleccionada"
    )
    answer_text = models.TextField(blank=True, verbose_name="Respuesta de Texto")
    is_correct = models.BooleanField(default=False, verbose_name="¿Es correcta?")
    points_earned = models.IntegerField(default=0, verbose_name="Puntos Obtenidos")
    
    class Meta:
        verbose_name = "Respuesta de Test"
        verbose_name_plural = "Respuestas de Tests"
        unique_together = ['attempt', 'question']
    
    def __str__(self):
        return f"{self.attempt} - {self.question}"

# ============================================================================
# MODELOS DE JUEGOS
# ============================================================================

class Game(BaseActivity):
    """Juegos educativos"""
    GAME_TYPES = [
        ('quiz', 'Cuestionario'),
        ('matching', 'Relacionar'),
        ('drag_drop', 'Arrastrar y Soltar'),
        ('puzzle', 'Rompecabezas'),
        ('memory', 'Memoria'),
        ('classification', 'Clasificación'),
        ('word_search', 'Sopa de Letras'),
        ('crossword', 'Crucigrama'),
    ]
    
    game_type = models.CharField(
        max_length=20,
        choices=GAME_TYPES,
        verbose_name="Tipo de Juego"
    )
    game_data = models.JSONField(
        default=dict,
        verbose_name="Datos del Juego",
        help_text="Configuración específica del juego en formato JSON"
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('easy', 'Fácil'),
            ('medium', 'Medio'),
            ('hard', 'Difícil'),
        ],
        default='medium',
        verbose_name="Nivel de Dificultad"
    )
    estimated_time = models.IntegerField(
        default=5,
        verbose_name="Tiempo Estimado (minutos)"
    )
    
    # Corregir related_name para evitar conflictos
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='created_games',
        verbose_name="Autor"
    )
    
    class Meta:
        verbose_name = "Juego"
        verbose_name_plural = "Juegos"

class GameSession(models.Model):
    """Sesiones de juego de estudiantes"""
    id = models.AutoField(primary_key=True)
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name="Juego"
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='game_sessions',
        verbose_name="Estudiante"
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Iniciado")
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name="Completado")
    score = models.IntegerField(default=0, verbose_name="Puntuación")
    max_score = models.IntegerField(default=0, verbose_name="Puntuación Máxima")
    time_spent = models.IntegerField(default=0, verbose_name="Tiempo Empleado (segundos)")
    is_completed = models.BooleanField(default=False, verbose_name="Completado")
    game_data = models.JSONField(
        default=dict,
        verbose_name="Datos de la Sesión"
    )
    
    class Meta:
        verbose_name = "Sesión de Juego"
        verbose_name_plural = "Sesiones de Juegos"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.game.title}"

# ============================================================================
# MODELOS DE ASIGNACIÓN A CLASES
# ============================================================================

class ClassroomActivity(models.Model):
    """Relación entre actividades y aulas"""
    id = models.AutoField(primary_key=True)
    classroom = models.ForeignKey(
        'gamification.Classroom',
        on_delete=models.CASCADE,
        related_name='educational_activities',
        verbose_name="Aula"
    )
    activity_type = models.CharField(
        max_length=20,
        choices=[
            ('assignment', 'Tarea'),
            ('reading', 'Lectura'),
            ('test', 'Test'),
            ('game', 'Juego'),
        ],
        verbose_name="Tipo de Actividad"
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Tarea"
    )
    reading = models.ForeignKey(
        Reading,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Lectura"
    )
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Test"
    )
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Juego"
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_activities',
        verbose_name="Asignado por"
    )
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Asignación")
    due_date = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de Vencimiento")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    
    class Meta:
        verbose_name = "Actividad de Aula"
        verbose_name_plural = "Actividades de Aula"
        unique_together = ['classroom', 'activity_type', 'assignment', 'reading', 'test', 'game']
    
    def __str__(self):
        activity_title = ""
        if self.assignment:
            activity_title = self.assignment.title
        elif self.reading:
            activity_title = self.reading.title
        elif self.test:
            activity_title = self.test.title
        elif self.game:
            activity_title = self.game.title
        
        return f"{self.classroom.name} - {activity_title}"
    
    def get_activity(self):
        """Obtiene la actividad específica"""
        if self.assignment:
            return self.assignment
        elif self.reading:
            return self.reading
        elif self.test:
            return self.test
        elif self.game:
            return self.game
        return None

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def generate_activity_code():
    """Genera un código único para actividades"""
    return str(uuid.uuid4())[:8].upper() 
 
 