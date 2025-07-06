from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()

# ============================================================================
# MODELOS BASE PARA EL SISTEMA DE GAMIFICACIÓN
# ============================================================================

class TipoActividad(models.Model):
    """Tipos de actividades disponibles"""
    IDtipoActividad = models.AutoField(primary_key=True)
    TipoActividad = models.CharField(max_length=100, verbose_name="Tipo de Actividad")
    
    def __str__(self):
        return self.TipoActividad
    
    class Meta:
        verbose_name = "Tipo de Actividad"
        verbose_name_plural = "Tipos de Actividades"

class TipoJuego(models.Model):
    """Tipos de juegos disponibles"""
    IDtipoJuego = models.IntegerField(primary_key=True)
    TipoJuego = models.CharField(max_length=50, verbose_name="Tipo de Juego")
    
    def __str__(self):
        return self.TipoJuego
    
    class Meta:
        verbose_name = "Tipo de Juego"
        verbose_name_plural = "Tipos de Juegos"

# ============================================================================
# MODELOS DE AULAS Y ACTIVIDADES
# ============================================================================

class Aulas(models.Model):
    """Aulas virtuales creadas por docentes"""
    IDaula = models.AutoField(primary_key=True)
    NombreAula = models.CharField(max_length=100, verbose_name="Nombre del Aula")
    CodigoAula = models.CharField(max_length=20, unique=True, verbose_name="Código del Aula")
    Descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    GradoEducativo = models.CharField(max_length=50, blank=True, null=True, verbose_name="Grado Educativo")
    Seccion = models.CharField(max_length=10, blank=True, null=True, verbose_name="Sección")
    IDinstitucion = models.IntegerField(default=1, verbose_name="ID de Institución")
    IDdocente = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Docente")
    FechaCreacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    
    def __str__(self):
        return f"{self.NombreAula} ({self.CodigoAula})"
    
    class Meta:
        verbose_name = "Aula"
        verbose_name_plural = "Aulas"

class AulaEstudiante(models.Model):
    """Relación entre estudiantes y aulas"""
    IDaula = models.ForeignKey(Aulas, on_delete=models.CASCADE, verbose_name="Aula")
    IDestudiante = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Estudiante")
    DenominacionAula = models.CharField(max_length=50, verbose_name="Denominación del Aula")
    
    class Meta:
        verbose_name = "Aula-Estudiante"
        verbose_name_plural = "Aulas-Estudiantes"
        unique_together = ('IDaula', 'IDestudiante')

class Actividades(models.Model):
    """Actividades asignadas por docentes a aulas"""
    IDactividad = models.AutoField(primary_key=True)
    Titulo = models.CharField(max_length=100, verbose_name="Título")
    Instrucciones = models.TextField(verbose_name="Instrucciones")
    IDtipoActividad = models.ForeignKey(TipoActividad, on_delete=models.CASCADE, verbose_name="Tipo de Actividad")
    IDficha = models.IntegerField(verbose_name="ID de Ficha")  # Referencia a content.Ficha
    IDaula = models.ForeignKey(Aulas, on_delete=models.CASCADE, verbose_name="Aula")
    
    def __str__(self):
        return self.Titulo
    
    class Meta:
        verbose_name = "Actividad"
        verbose_name_plural = "Actividades"

# ============================================================================
# MODELOS DE JUEGOS
# ============================================================================

class Juegos(models.Model):
    """Juegos educativos disponibles"""
    IDjuego = models.AutoField(primary_key=True)
    NombreJuego = models.CharField(max_length=100, verbose_name="Nombre del Juego")
    IDtipoJuego = models.ForeignKey(TipoJuego, on_delete=models.CASCADE, verbose_name="Tipo de Juego")
    Instrucciones = models.CharField(max_length=500, verbose_name="Instrucciones")
    Descripcion = models.CharField(max_length=50, verbose_name="Descripción")
    NivelDificultad = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Nivel de Dificultad"
    )
    
    def __str__(self):
        return self.NombreJuego
    
    class Meta:
        verbose_name = "Juego"
        verbose_name_plural = "Juegos"

class JuegoUsuario(models.Model):
    """Progreso de usuarios en juegos"""
    IDusuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario")
    IDjuego = models.ForeignKey(Juegos, on_delete=models.CASCADE, verbose_name="Juego")
    Puntaje = models.IntegerField(default=0, verbose_name="Puntaje")
    FechaJugada = models.DateTimeField(auto_now_add=True, verbose_name="Fecha Jugada")
    
    class Meta:
        verbose_name = "Juego Usuario"
        verbose_name_plural = "Juegos Usuario"
        unique_together = ('IDusuario', 'IDjuego', 'FechaJugada')

# ============================================================================
# MODELOS DE PROGRESO Y NIVELES
# ============================================================================

class Progreso(models.Model):
    """Progreso de usuarios en actividades"""
    IDprogreso = models.AutoField(primary_key=True)
    IDusuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario")
    IDactividad = models.ForeignKey(Actividades, on_delete=models.CASCADE, verbose_name="Actividad")
    Fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    Puntuacion = models.IntegerField(default=0, verbose_name="Puntuación")
    Completado = models.BooleanField(default=False, verbose_name="Completado")
    
    def __str__(self):
        return f"{self.IDusuario} - {self.IDactividad} ({self.Puntuacion} pts)"
    
    class Meta:
        verbose_name = "Progreso"
        verbose_name_plural = "Progresos"

class Niveles(models.Model):
    """Sistema de niveles para usuarios"""
    IDusuario = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, verbose_name="Usuario")
    nivel = models.IntegerField(default=1, verbose_name="Nivel")
    puntos_acumulados = models.IntegerField(default=0, verbose_name="Puntos Acumulados")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")
    
    def __str__(self):
        return f"{self.IDusuario} - Nivel {self.nivel} ({self.puntos_acumulados} pts)"
    
    def calcular_nivel(self):
        """Calcula el nivel basado en los puntos acumulados"""
        if self.puntos_acumulados < 20:
            return 1
        elif self.puntos_acumulados < 50:
            return 2
        elif self.puntos_acumulados < 100:
            return 3
        elif self.puntos_acumulados < 200:
            return 4
        elif self.puntos_acumulados < 350:
            return 5
        elif self.puntos_acumulados < 550:
            return 6
        elif self.puntos_acumulados < 800:
            return 7
        elif self.puntos_acumulados < 1100:
            return 8
        elif self.puntos_acumulados < 1450:
            return 9
        else:
            return 10
    
    def actualizar_nivel(self):
        """Actualiza el nivel basado en los puntos"""
        nuevo_nivel = self.calcular_nivel()
        if nuevo_nivel != self.nivel:
            self.nivel = nuevo_nivel
            self.save()
            return True
        return False
    
    class Meta:
        verbose_name = "Nivel"
        verbose_name_plural = "Niveles"

# ============================================================================
# MODELOS DE INSIGNIAS
# ============================================================================

class Insignias(models.Model):
    """Insignias que los usuarios pueden ganar"""
    IDinsignia = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.TextField(verbose_name="Descripción")
    imagen = models.ImageField(upload_to='insignias/', blank=True, null=True, verbose_name="Imagen")
    condicion = models.CharField(max_length=200, verbose_name="Condición")
    puntos_requeridos = models.IntegerField(default=0, verbose_name="Puntos Requeridos")
    
    # Tipos de insignias
    TIPOS_INSIGNIA = [
        ('especies_expert', 'Experto en Especies'),
        ('quiz_master', 'Maestro de Cuestionarios'),
        ('speed_demon', 'Demonio de Velocidad'),
        ('explorer', 'Explorador'),
        ('conservationist', 'Conservacionista'),
        ('collector', 'Coleccionista'),
        ('first_activity', 'Primera Actividad'),
        ('perfect_score', 'Puntuación Perfecta'),
        ('streak_3', 'Racha de 3'),
        ('streak_7', 'Racha de 7'),
        ('streak_30', 'Racha de 30'),
    ]
    tipo_insignia = models.CharField(max_length=20, choices=TIPOS_INSIGNIA, verbose_name="Tipo de Insignia")
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Insignia"
        verbose_name_plural = "Insignias"

class InsigniasUsuario(models.Model):
    """Relación entre usuarios e insignias obtenidas"""
    IDusuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario")
    IDinsignia = models.ForeignKey(Insignias, on_delete=models.CASCADE, verbose_name="Insignia")
    fecha_obtenida = models.DateTimeField(auto_now_add=True, verbose_name="Fecha Obtenida")
    
    class Meta:
        verbose_name = "Insignia Usuario"
        verbose_name_plural = "Insignias Usuario"
        unique_together = ('IDusuario', 'IDinsignia')

# ============================================================================
# MODELOS DE DESAFÍOS Y MISIONES
# ============================================================================

class Desafios(models.Model):
    """Desafíos opcionales para usuarios"""
    IDdesafio = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.TextField(verbose_name="Descripción")
    puntos = models.IntegerField(default=0, verbose_name="Puntos")
    nivel_minimo = models.IntegerField(default=1, verbose_name="Nivel Mínimo")
    
    # Tipos de desafíos
    TIPOS_DESAFIO = [
        ('diario', 'Diario'),
        ('semanal', 'Semanal'),
        ('especial', 'Especial'),
    ]
    tipo_desafio = models.CharField(max_length=20, choices=TIPOS_DESAFIO, verbose_name="Tipo de Desafío")
    
    # Condiciones del desafío
    condicion = models.CharField(max_length=200, verbose_name="Condición")
    fecha_inicio = models.DateTimeField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateTimeField(verbose_name="Fecha de Fin")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Desafío"
        verbose_name_plural = "Desafíos"

class DesafiosUsuario(models.Model):
    """Progreso de usuarios en desafíos"""
    IDusuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario")
    IDdesafio = models.ForeignKey(Desafios, on_delete=models.CASCADE, verbose_name="Desafío")
    completado = models.BooleanField(default=False, verbose_name="Completado")
    fecha_completado = models.DateTimeField(null=True, blank=True, verbose_name="Fecha Completado")
    progreso_actual = models.IntegerField(default=0, verbose_name="Progreso Actual")
    
    class Meta:
        verbose_name = "Desafío Usuario"
        verbose_name_plural = "Desafíos Usuario"
        unique_together = ('IDusuario', 'IDdesafio')

# ============================================================================
# MODELOS DE RANKINGS Y CLASIFICACIONES
# ============================================================================

class Ranking(models.Model):
    """Ranking de usuarios por aula"""
    IDranking = models.AutoField(primary_key=True)
    IDaula = models.ForeignKey(Aulas, on_delete=models.CASCADE, verbose_name="Aula")
    IDusuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario")
    puntos_totales = models.IntegerField(default=0, verbose_name="Puntos Totales")
    nivel_actual = models.IntegerField(default=1, verbose_name="Nivel Actual")
    posicion = models.IntegerField(verbose_name="Posición")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")
    
    class Meta:
        verbose_name = "Ranking"
        verbose_name_plural = "Rankings"
        unique_together = ('IDaula', 'IDusuario')
        ordering = ['-puntos_totales', 'nivel_actual']

# ============================================================================
# MODELOS DE RECOMPENSAS
# ============================================================================

class RecompensasUsuario(models.Model):
    """Recompensas obtenidas por usuarios"""
    IDusuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario")
    IDjuego = models.ForeignKey(Juegos, on_delete=models.CASCADE, verbose_name="Juego")
    FechaObtenida = models.DateTimeField(auto_now_add=True, verbose_name="Fecha Obtenida")
    
    class Meta:
        verbose_name = "Recompensa Usuario"
        verbose_name_plural = "Recompensas Usuario"
        unique_together = ('IDusuario', 'IDjuego')

# ============================================================================
# MODELOS DE ESTADÍSTICAS Y SEGUIMIENTO
# ============================================================================

class EstadisticasUsuario(models.Model):
    """Estadísticas detalladas de usuarios"""
    IDusuario = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, verbose_name="Usuario")
    actividades_completadas = models.IntegerField(default=0, verbose_name="Actividades Completadas")
    juegos_jugados = models.IntegerField(default=0, verbose_name="Juegos Jugados")
    insignias_obtenidas = models.IntegerField(default=0, verbose_name="Insignias Obtenidas")
    desafios_completados = models.IntegerField(default=0, verbose_name="Desafíos Completados")
    tiempo_total_juego = models.IntegerField(default=0, verbose_name="Tiempo Total de Juego (minutos)")
    puntuacion_total = models.IntegerField(default=0, verbose_name="Puntuación Total")
    racha_actual = models.IntegerField(default=0, verbose_name="Racha Actual")
    mejor_racha = models.IntegerField(default=0, verbose_name="Mejor Racha")
    fecha_ultima_actividad = models.DateTimeField(auto_now=True, verbose_name="Última Actividad")
    
    def __str__(self):
        return f"Estadísticas de {self.IDusuario}"
    
    class Meta:
        verbose_name = "Estadística Usuario"
        verbose_name_plural = "Estadísticas Usuario"

# ============================================================================
# MODELOS DE CONFIGURACIÓN
# ============================================================================

class ConfiguracionGamificacion(models.Model):
    """Configuración del sistema de gamificación"""
    IDconfiguracion = models.AutoField(primary_key=True)
    nombre_configuracion = models.CharField(max_length=100, verbose_name="Nombre de Configuración")
    valor = models.TextField(verbose_name="Valor")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    
    def __str__(self):
        return self.nombre_configuracion

    class Meta:
        verbose_name = "Configuración Gamificación"
        verbose_name_plural = "Configuraciones Gamificación"

# ============================================================================
# MODELOS DE LOGS Y AUDITORÍA
# ============================================================================

class LogGamificacion(models.Model):
    """Log de eventos de gamificación"""
    IDlog = models.AutoField(primary_key=True)
    IDusuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario")
    tipo_evento = models.CharField(max_length=50, verbose_name="Tipo de Evento")
    descripcion = models.TextField(verbose_name="Descripción")
    puntos_ganados = models.IntegerField(default=0, verbose_name="Puntos Ganados")
    fecha_evento = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del Evento")
    
    class Meta:
        verbose_name = "Log Gamificación"
        verbose_name_plural = "Logs Gamificación"
        ordering = ['-fecha_evento']

# ============================================================================
# MODELOS DE TESTS Y CUESTIONARIOS
# ============================================================================

class Test(models.Model):
    """Tests creados por docentes para aulas específicas"""
    IDtest = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=200, verbose_name="Título del Test")
    descripcion = models.TextField(verbose_name="Descripción")
    IDaula = models.ForeignKey(Aulas, on_delete=models.CASCADE, verbose_name="Aula")
    IDdocente = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Docente")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_inicio = models.DateTimeField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateTimeField(verbose_name="Fecha de Fin")
    tiempo_limite = models.IntegerField(default=30, verbose_name="Tiempo Límite (minutos)")
    puntos_por_pregunta = models.IntegerField(default=10, verbose_name="Puntos por Pregunta")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    
    def __str__(self):
        return f"{self.titulo} - {self.IDaula.NombreAula}"
    
    class Meta:
        verbose_name = "Test"
        verbose_name_plural = "Tests"
        ordering = ['-fecha_creacion']

class Pregunta(models.Model):
    """Preguntas de los tests"""
    IDpregunta = models.AutoField(primary_key=True)
    IDtest = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name="Test")
    pregunta = models.TextField(verbose_name="Pregunta")
    tipo_pregunta = models.CharField(
        max_length=20,
        choices=[
            ('opcion_multiple', 'Opción Múltiple'),
            ('verdadero_falso', 'Verdadero/Falso'),
            ('texto_corto', 'Texto Corto'),
        ],
        default='opcion_multiple',
        verbose_name="Tipo de Pregunta"
    )
    orden = models.IntegerField(default=1, verbose_name="Orden")
    puntos = models.IntegerField(default=10, verbose_name="Puntos")

    def __str__(self):
        return f"{self.IDtest.titulo} - Pregunta {self.orden}"

    class Meta:
        verbose_name = "Pregunta"
        verbose_name_plural = "Preguntas"
        ordering = ['IDtest', 'orden']

class Opcion(models.Model):
    """Opciones de respuesta para preguntas de opción múltiple"""
    IDopcion = models.AutoField(primary_key=True)
    IDpregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, verbose_name="Pregunta")
    texto = models.CharField(max_length=500, verbose_name="Texto de la Opción")
    es_correcta = models.BooleanField(default=False, verbose_name="Es Correcta")
    orden = models.IntegerField(default=1, verbose_name="Orden")

    def __str__(self):
        return f"{self.IDpregunta.pregunta[:50]} - {self.texto[:30]}"

    class Meta:
        verbose_name = "Opción"
        verbose_name_plural = "Opciones"
        ordering = ['IDpregunta', 'orden']

class RespuestaEstudiante(models.Model):
    """Respuestas de estudiantes a tests"""
    IDrespuesta = models.AutoField(primary_key=True)
    IDtest = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name="Test")
    IDpregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, verbose_name="Pregunta")
    IDestudiante = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Estudiante")
    respuesta_texto = models.TextField(blank=True, null=True, verbose_name="Respuesta de Texto")
    IDopcion_seleccionada = models.ForeignKey(
        Opcion, 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True, 
        verbose_name="Opción Seleccionada"
    )
    es_correcta = models.BooleanField(default=False, verbose_name="Es Correcta")
    puntos_obtenidos = models.IntegerField(default=0, verbose_name="Puntos Obtenidos")
    fecha_respuesta = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Respuesta")

    def __str__(self):
        return f"{self.IDestudiante.username} - {self.IDtest.titulo}"

    class Meta:
        verbose_name = "Respuesta de Estudiante"
        verbose_name_plural = "Respuestas de Estudiantes"
        unique_together = ['IDtest', 'IDpregunta', 'IDestudiante']

class ResultadoTest(models.Model):
    """Resultados completos de estudiantes en tests"""
    IDresultado = models.AutoField(primary_key=True)
    IDtest = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name="Test")
    IDestudiante = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Estudiante")
    puntuacion_total = models.IntegerField(default=0, verbose_name="Puntuación Total")
    puntuacion_maxima = models.IntegerField(default=0, verbose_name="Puntuación Máxima")
    porcentaje_acierto = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0, 
        verbose_name="Porcentaje de Acierto"
    )
    preguntas_correctas = models.IntegerField(default=0, verbose_name="Preguntas Correctas")
    total_preguntas = models.IntegerField(default=0, verbose_name="Total de Preguntas")
    tiempo_empleado = models.IntegerField(default=0, verbose_name="Tiempo Empleado (segundos)")
    fecha_inicio = models.DateTimeField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateTimeField(verbose_name="Fecha de Fin")
    completado = models.BooleanField(default=False, verbose_name="Completado")

    def __str__(self):
        return f"{self.IDestudiante.username} - {self.IDtest.titulo} ({self.porcentaje_acierto}%)"

    class Meta:
        verbose_name = "Resultado de Test"
        verbose_name_plural = "Resultados de Tests"
        unique_together = ['IDtest', 'IDestudiante']
        ordering = ['-fecha_fin']

# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def generar_codigo_aula():
    """Genera un código único para aulas"""
    return str(uuid.uuid4())[:8].upper()

def calcular_puntos_por_nivel(nivel):
    """Calcula los puntos necesarios para un nivel específico"""
    if nivel == 1:
        return 0
    elif nivel == 2:
        return 20
    elif nivel == 3:
        return 50
    elif nivel == 4:
        return 100
    elif nivel == 5:
        return 200
    elif nivel == 6:
        return 350
    elif nivel == 7:
        return 550
    elif nivel == 8:
        return 800
    elif nivel == 9:
        return 1100
    else:
        return 1450

# ============================================================================
# FUNCIONES DE UTILIDAD PARA TESTS
# ============================================================================

def calcular_puntuacion_test(resultado):
    """Calcula la puntuación total de un test"""
    respuestas = RespuestaEstudiante.objects.filter(
        IDtest=resultado.IDtest,
        IDestudiante=resultado.IDestudiante
    )
    puntuacion = sum(r.puntos_obtenidos for r in respuestas)
    return puntuacion

def calcular_porcentaje_acierto(resultado):
    """Calcula el porcentaje de acierto de un test"""
    if resultado.total_preguntas == 0:
        return 0
    return (resultado.preguntas_correctas / resultado.total_preguntas) * 100
