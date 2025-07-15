from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Niveles, Insignias, InsigniasUsuario, LogGamificacion, ConfiguracionGamificacion
from datetime import timedelta

User = get_user_model()

def get_puntos_por_nivel(nivel_actual):
    """
    Obtiene los puntos por actividad según el nivel actual
    """
    if nivel_actual == 1:
        return 5  # Nivel 1: 0-20 puntos
    elif nivel_actual == 2:
        return 10  # Nivel 2: 20-50 puntos
    elif nivel_actual == 3:
        return 15  # Nivel 3: 50-100 puntos
    elif nivel_actual == 4:
        return 20  # Nivel 4: 100-500 puntos
    else:
        # Niveles superiores: 25 + 5 por cada nivel adicional
        return 25 + (nivel_actual - 4) * 5

def calcular_nivel(puntos_acumulados):
    """
    Calcula el nivel basado en los puntos acumulados
    """
    if puntos_acumulados < 20:
        return 1
    elif puntos_acumulados < 50:
        return 2
    elif puntos_acumulados < 100:
        return 3
    elif puntos_acumulados < 500:
        return 4
    else:
        # Niveles superiores: cada 200 puntos adicionales
        nivel_extra = (puntos_acumulados - 500) // 200
        return 5 + nivel_extra

def asignar_puntuacion_actividad(user, actividad_tipo, puntuacion_porcentaje=100, bonus_racha=0):
    """
    Asigna puntuación por completar una actividad
    """
    try:
        # Obtener o crear nivel del usuario
        nivel_obj, created = Niveles.objects.get_or_create(
            IDusuario=user,
            defaults={
                'nivel': 1,
                'puntos_acumulados': 0,
                'fecha_actualizacion': timezone.now()
            }
        )
        
        # Calcular puntos base según nivel actual
        puntos_base = get_puntos_por_nivel(nivel_obj.nivel)
        
        # Ajustar puntos según porcentaje de acierto
        puntos_ajustados = int(puntos_base * (puntuacion_porcentaje / 100))
        
        # Agregar bonus por racha
        puntos_totales = puntos_ajustados + bonus_racha
        
        # Actualizar puntos acumulados
        nivel_obj.puntos_acumulados += puntos_totales
        
        # Calcular nuevo nivel
        nuevo_nivel = calcular_nivel(nivel_obj.puntos_acumulados)
        
        # Verificar si subió de nivel
        subio_nivel = nuevo_nivel > nivel_obj.nivel
        
        # Actualizar nivel si cambió
        if subio_nivel:
            nivel_obj.nivel = nuevo_nivel
        
        nivel_obj.fecha_actualizacion = timezone.now()
        nivel_obj.save()
        
        # Registrar en log
        LogGamificacion.objects.create(
            IDusuario=user,
            tipo_evento='activity_completed',
            descripcion=f'Completó actividad: {actividad_tipo}',
            puntos_ganados=puntos_totales,
            fecha_evento=timezone.now()
        )
        
        # Verificar insignias desbloqueadas
        insignias_desbloqueadas = verificar_insignias(user, nivel_obj.puntos_acumulados)
        
        return {
            'puntos_ganados': puntos_totales,
            'puntos_acumulados': nivel_obj.puntos_acumulados,
            'nivel_actual': nivel_obj.nivel,
            'subio_nivel': subio_nivel,
            'insignias_desbloqueadas': insignias_desbloqueadas
        }
        
    except Exception as e:
        print(f"Error al asignar puntuación: {e}")
        return None

def verificar_insignias(user, puntos_acumulados):
    """
    Verifica si el usuario ha desbloqueado nuevas insignias
    """
    insignias_desbloqueadas = []
    
    # Obtener insignias que el usuario puede desbloquear
    insignias_disponibles = Insignias.objects.filter(
        puntos_requeridos__lte=puntos_acumulados
    )
    
    for insignia in insignias_disponibles:
        # Verificar si ya tiene la insignia
        if not InsigniasUsuario.objects.filter(
            IDusuario=user,
            IDinsignia=insignia
        ).exists():
            # Asignar insignia
            InsigniasUsuario.objects.create(
                IDusuario=user,
                IDinsignia=insignia,
                fecha_obtenida=timezone.now()
            )
            
            insignias_desbloqueadas.append({
                'nombre': insignia.nombre,
                'descripcion': insignia.descripcion,
                'puntos_requeridos': insignia.puntos_requeridos
            })
            
            # Registrar en log
            LogGamificacion.objects.create(
                IDusuario=user,
                tipo_evento='achievement_unlocked',
                descripcion=f'Desbloqueó insignia: {insignia.nombre}',
                puntos_ganados=0,
                fecha_evento=timezone.now()
            )
    
    return insignias_desbloqueadas

def calcular_bonus_racha(user, actividades_consecutivas):
    """
    Calcula bonus por racha de actividades consecutivas
    """
    if actividades_consecutivas >= 30:
        return 200  # Racha de 30
    elif actividades_consecutivas >= 7:
        return 50   # Racha de 7
    elif actividades_consecutivas >= 3:
        return 15   # Racha de 3
    else:
        return 0

def asignar_puntuacion_perfecta(user, actividad_tipo):
    """
    Asigna puntos bonus por puntuación perfecta (100%)
    """
    try:
        nivel_obj = Niveles.objects.get(IDusuario=user)
        puntos_bonus = 25  # Bonus por puntuación perfecta
        
        nivel_obj.puntos_acumulados += puntos_bonus
        nivel_obj.save()
        
        # Registrar en log
        LogGamificacion.objects.create(
            IDusuario=user,
            tipo_evento='perfect_score',
            descripcion=f'Puntuación perfecta en: {actividad_tipo}',
            puntos_ganados=puntos_bonus,
            fecha_evento=timezone.now()
        )
        
        return puntos_bonus
        
    except Exception as e:
        print(f"Error al asignar puntuación perfecta: {e}")
        return 0

def obtener_estadisticas_usuario(user):
    """
    Obtiene estadísticas completas del usuario
    """
    try:
        nivel_obj = Niveles.objects.get(IDusuario=user)
        
        # Obtener insignias del usuario
        insignias_usuario = InsigniasUsuario.objects.filter(IDusuario=user)
        
        # Obtener log de actividades recientes
        actividades_recientes = LogGamificacion.objects.filter(
            IDusuario=user,
            tipo_evento='activity_completed'
        ).order_by('-fecha_evento')[:10]
        
        # Calcular progreso hacia el siguiente nivel
        puntos_actuales = nivel_obj.puntos_acumulados
        nivel_actual = nivel_obj.nivel
        
        if nivel_actual == 1:
            puntos_siguiente_nivel = 20
        elif nivel_actual == 2:
            puntos_siguiente_nivel = 50
        elif nivel_actual == 3:
            puntos_siguiente_nivel = 100
        elif nivel_actual == 4:
            puntos_siguiente_nivel = 500
        else:
            # Niveles superiores
            puntos_siguiente_nivel = 500 + (nivel_actual - 4) * 200
        
        progreso_porcentaje = min(100, (puntos_actuales / puntos_siguiente_nivel) * 100)
        
        return {
            'nivel_actual': nivel_actual,
            'puntos_acumulados': puntos_actuales,
            'puntos_siguiente_nivel': puntos_siguiente_nivel,
            'progreso_porcentaje': progreso_porcentaje,
            'insignias_obtenidas': insignias_usuario.count(),
            'actividades_recientes': actividades_recientes,
            'puntos_por_actividad': get_puntos_por_nivel(nivel_actual)
        }
        
    except Niveles.DoesNotExist:
        return None

def crear_nivel_usuario(user):
    """
    Crea un registro de nivel para un usuario si no existe
    """
    nivel_obj, created = Niveles.objects.get_or_create(
        IDusuario=user,
        defaults={
            'nivel': 1,
            'puntos_acumulados': 0,
            'fecha_actualizacion': timezone.now()
        }
    )
    return nivel_obj 