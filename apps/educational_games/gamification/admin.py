from django.contrib import admin
from .models import (
    TipoActividad, TipoJuego, Aulas, AulaEstudiante, Actividades,
    Juegos, JuegoUsuario, Progreso, Niveles, Insignias, InsigniasUsuario,
    Desafios, DesafiosUsuario, Ranking, RecompensasUsuario,
    EstadisticasUsuario, ConfiguracionGamificacion, LogGamificacion,
    Test, Pregunta, Opcion, RespuestaEstudiante, ResultadoTest
)

# ============================================================================
# ADMINISTRACIÓN DE TIPOS
# ============================================================================

@admin.register(TipoActividad)
class TipoActividadAdmin(admin.ModelAdmin):
    list_display = ['IDtipoActividad', 'TipoActividad']
    search_fields = ['TipoActividad']
    ordering = ['TipoActividad']

@admin.register(TipoJuego)
class TipoJuegoAdmin(admin.ModelAdmin):
    list_display = ['IDtipoJuego', 'TipoJuego']
    search_fields = ['TipoJuego']
    ordering = ['TipoJuego']

# ============================================================================
# ADMINISTRACIÓN DE AULAS
# ============================================================================

@admin.register(Aulas)
class AulasAdmin(admin.ModelAdmin):
    list_display = ['IDaula', 'NombreAula', 'CodigoAula', 'IDdocente', 'FechaCreacion']
    list_filter = ['FechaCreacion']
    search_fields = ['NombreAula', 'CodigoAula', 'IDdocente__username']
    readonly_fields = ['FechaCreacion']
    ordering = ['-FechaCreacion']

@admin.register(AulaEstudiante)
class AulaEstudianteAdmin(admin.ModelAdmin):
    list_display = ['IDaula', 'IDestudiante', 'DenominacionAula']
    list_filter = ['IDaula']
    search_fields = ['IDestudiante__username', 'IDaula__NombreAula']
    ordering = ['IDaula', 'IDestudiante']

# ============================================================================
# ADMINISTRACIÓN DE ACTIVIDADES
# ============================================================================

@admin.register(Actividades)
class ActividadesAdmin(admin.ModelAdmin):
    list_display = ['IDactividad', 'Titulo', 'IDtipoActividad', 'IDaula', 'IDficha']
    list_filter = ['IDtipoActividad', 'IDaula']
    search_fields = ['Titulo', 'Instrucciones']
    ordering = ['-IDactividad']

# ============================================================================
# ADMINISTRACIÓN DE JUEGOS
# ============================================================================

@admin.register(Juegos)
class JuegosAdmin(admin.ModelAdmin):
    list_display = ['IDjuego', 'NombreJuego', 'IDtipoJuego', 'NivelDificultad', 'Descripcion']
    list_filter = ['IDtipoJuego', 'NivelDificultad']
    search_fields = ['NombreJuego', 'Descripcion', 'Instrucciones']
    ordering = ['IDjuego']

@admin.register(JuegoUsuario)
class JuegoUsuarioAdmin(admin.ModelAdmin):
    list_display = ['IDusuario', 'IDjuego', 'Puntaje', 'FechaJugada']
    list_filter = ['IDjuego', 'FechaJugada']
    search_fields = ['IDusuario__username', 'IDjuego__NombreJuego']
    readonly_fields = ['FechaJugada']
    ordering = ['-FechaJugada']

# ============================================================================
# ADMINISTRACIÓN DE PROGRESO Y NIVELES
# ============================================================================

@admin.register(Progreso)
class ProgresoAdmin(admin.ModelAdmin):
    list_display = ['IDprogreso', 'IDusuario', 'IDactividad', 'Puntuacion', 'Completado', 'Fecha']
    list_filter = ['Completado', 'Fecha', 'IDactividad']
    search_fields = ['IDusuario__username', 'IDactividad__Titulo']
    readonly_fields = ['Fecha']
    ordering = ['-Fecha']

@admin.register(Niveles)
class NivelesAdmin(admin.ModelAdmin):
    list_display = ['IDusuario', 'nivel', 'puntos_acumulados', 'fecha_actualizacion']
    list_filter = ['nivel', 'fecha_actualizacion']
    search_fields = ['IDusuario__username']
    readonly_fields = ['fecha_actualizacion']
    ordering = ['-puntos_acumulados']

# ============================================================================
# ADMINISTRACIÓN DE INSIGNIAS
# ============================================================================

@admin.register(Insignias)
class InsigniasAdmin(admin.ModelAdmin):
    list_display = ['IDinsignia', 'nombre', 'tipo_insignia', 'puntos_requeridos']
    list_filter = ['tipo_insignia']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']

@admin.register(InsigniasUsuario)
class InsigniasUsuarioAdmin(admin.ModelAdmin):
    list_display = ['IDusuario', 'IDinsignia', 'fecha_obtenida']
    list_filter = ['IDinsignia', 'fecha_obtenida']
    search_fields = ['IDusuario__username', 'IDinsignia__nombre']
    readonly_fields = ['fecha_obtenida']
    ordering = ['-fecha_obtenida']

# ============================================================================
# ADMINISTRACIÓN DE DESAFÍOS
# ============================================================================

@admin.register(Desafios)
class DesafiosAdmin(admin.ModelAdmin):
    list_display = ['IDdesafio', 'nombre', 'tipo_desafio', 'puntos', 'nivel_minimo', 'activo']
    list_filter = ['tipo_desafio', 'activo', 'fecha_inicio', 'fecha_fin']
    search_fields = ['nombre', 'descripcion']
    ordering = ['-fecha_inicio']

@admin.register(DesafiosUsuario)
class DesafiosUsuarioAdmin(admin.ModelAdmin):
    list_display = ['IDusuario', 'IDdesafio', 'completado', 'progreso_actual', 'fecha_completado']
    list_filter = ['completado', 'IDdesafio']
    search_fields = ['IDusuario__username', 'IDdesafio__nombre']
    readonly_fields = ['fecha_completado']

# ============================================================================
# ADMINISTRACIÓN DE RANKINGS
# ============================================================================

@admin.register(Ranking)
class RankingAdmin(admin.ModelAdmin):
    list_display = ['IDranking', 'IDaula', 'IDusuario', 'puntos_totales', 'nivel_actual', 'posicion']
    list_filter = ['IDaula', 'nivel_actual']
    search_fields = ['IDusuario__username', 'IDaula__NombreAula']
    readonly_fields = ['fecha_actualizacion']
    ordering = ['IDaula', '-puntos_totales']

# ============================================================================
# ADMINISTRACIÓN DE RECOMPENSAS
# ============================================================================

@admin.register(RecompensasUsuario)
class RecompensasUsuarioAdmin(admin.ModelAdmin):
    list_display = ['IDusuario', 'IDjuego', 'FechaObtenida']
    list_filter = ['IDjuego', 'FechaObtenida']
    search_fields = ['IDusuario__username', 'IDjuego__NombreJuego']
    readonly_fields = ['FechaObtenida']
    ordering = ['-FechaObtenida']

# ============================================================================
# ADMINISTRACIÓN DE ESTADÍSTICAS
# ============================================================================

@admin.register(EstadisticasUsuario)
class EstadisticasUsuarioAdmin(admin.ModelAdmin):
    list_display = [
        'IDusuario', 'actividades_completadas', 'juegos_jugados', 
        'insignias_obtenidas', 'puntuacion_total'
    ]
    list_filter = ['fecha_ultima_actividad']
    search_fields = ['IDusuario__username']
    readonly_fields = ['fecha_ultima_actividad']
    ordering = ['-puntuacion_total']

# ============================================================================
# ADMINISTRACIÓN DE CONFIGURACIÓN
# ============================================================================

@admin.register(ConfiguracionGamificacion)
class ConfiguracionGamificacionAdmin(admin.ModelAdmin):
    list_display = ['IDconfiguracion', 'nombre_configuracion', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre_configuracion', 'descripcion']
    ordering = ['nombre_configuracion']

# ============================================================================
# ADMINISTRACIÓN DE LOGS
# ============================================================================

@admin.register(LogGamificacion)
class LogGamificacionAdmin(admin.ModelAdmin):
    list_display = ['IDlog', 'IDusuario', 'tipo_evento', 'puntos_ganados', 'fecha_evento']
    list_filter = ['tipo_evento', 'fecha_evento']
    search_fields = ['IDusuario__username', 'descripcion']
    readonly_fields = ['fecha_evento']
    ordering = ['-fecha_evento']

# ============================================================================
# ADMINISTRACIÓN DE TESTS Y CUESTIONARIOS
# ============================================================================

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['IDtest', 'titulo', 'IDaula', 'IDdocente', 'fecha_creacion', 'activo']
    list_filter = ['activo', 'fecha_creacion', 'fecha_inicio', 'fecha_fin', 'IDaula']
    search_fields = ['titulo', 'descripcion', 'IDaula__NombreAula', 'IDdocente__username']
    readonly_fields = ['fecha_creacion']
    ordering = ['-fecha_creacion']
    date_hierarchy = 'fecha_creacion'

@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ['IDpregunta', 'IDtest', 'pregunta', 'tipo_pregunta', 'orden', 'puntos']
    list_filter = ['tipo_pregunta', 'IDtest']
    search_fields = ['pregunta', 'IDtest__titulo']
    ordering = ['IDtest', 'orden']

@admin.register(Opcion)
class OpcionAdmin(admin.ModelAdmin):
    list_display = ['IDopcion', 'IDpregunta', 'texto', 'es_correcta', 'orden']
    list_filter = ['es_correcta', 'IDpregunta__IDtest']
    search_fields = ['texto', 'IDpregunta__pregunta']
    ordering = ['IDpregunta', 'orden']

@admin.register(RespuestaEstudiante)
class RespuestaEstudianteAdmin(admin.ModelAdmin):
    list_display = ['IDrespuesta', 'IDtest', 'IDpregunta', 'IDestudiante', 'es_correcta', 'puntos_obtenidos', 'fecha_respuesta']
    list_filter = ['es_correcta', 'fecha_respuesta', 'IDtest']
    search_fields = ['IDestudiante__username', 'IDtest__titulo', 'IDpregunta__pregunta']
    readonly_fields = ['fecha_respuesta']
    ordering = ['-fecha_respuesta']

@admin.register(ResultadoTest)
class ResultadoTestAdmin(admin.ModelAdmin):
    list_display = ['IDresultado', 'IDtest', 'IDestudiante', 'puntuacion_total', 'porcentaje_acierto', 'completado', 'fecha_fin']
    list_filter = ['completado', 'fecha_fin', 'IDtest']
    search_fields = ['IDestudiante__username', 'IDtest__titulo']
    readonly_fields = ['fecha_fin']
    ordering = ['-fecha_fin'] 