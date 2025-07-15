from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.core.paginator import Paginator
import json

User = get_user_model()

from .models import (
    Juegos, JuegoUsuario, Progreso, Niveles, Insignias, InsigniasUsuario,
    Aulas, AulaEstudiante, Actividades, TipoActividad, TipoJuego,
    Desafios, DesafiosUsuario, Ranking, RecompensasUsuario,
    EstadisticasUsuario, LogGamificacion, Test, Pregunta, Opcion, RespuestaEstudiante, ResultadoTest
)
from apps.animals.models import Animal
from apps.plants.models import Plant
from apps.common.models import Category, Location

# ============================================================================
# VISTAS PRINCIPALES
# ============================================================================

@login_required
def dashboard(request):
    """Dashboard principal de gamification"""
    user = request.user
    
    # Obtener o crear nivel del usuario
    nivel, created = Niveles.objects.get_or_create(IDusuario=user)
    
    # Obtener o crear estadísticas del usuario
    estadisticas, created = EstadisticasUsuario.objects.get_or_create(IDusuario=user)
    
    # Obtener insignias del usuario
    insignias_usuario = InsigniasUsuario.objects.filter(IDusuario=user)
    
    # Juegos más populares
    popular_games = Juegos.objects.annotate(
        play_count=Count('juegousuario')
    ).order_by('-play_count')[:5]
    
    # Juegos recientes del usuario
    recent_sessions = JuegoUsuario.objects.filter(IDusuario=user).order_by('-FechaJugada')[:5]
    
    # Aulas del usuario (si es estudiante)
    aulas_usuario = []
    if hasattr(user, 'aulas'):
        aulas_usuario = user.aulas.all()
    
    # Actividades asignadas al usuario
    actividades_asignadas = []
    for aula_estudiante in AulaEstudiante.objects.filter(IDestudiante=user):
        actividades_asignadas.extend(aula_estudiante.IDaula.actividades_set.all())
    
    # Desafíos disponibles
    desafios_disponibles = Desafios.objects.filter(
        activo=True,
        nivel_minimo__lte=nivel.nivel,
        fecha_inicio__lte=timezone.now(),
        fecha_fin__gte=timezone.now()
    )
    
    context = {
        'total_games_played': estadisticas.juegos_jugados,
        'total_points': nivel.puntos_acumulados,
        'user_level': nivel.nivel,
        'user_badges': insignias_usuario,
        'popular_games': popular_games,
        'recent_sessions': recent_sessions,
        'aulas_usuario': aulas_usuario,
        'actividades_asignadas': actividades_asignadas,
        'desafios_disponibles': desafios_disponibles,
        'estadisticas': estadisticas,
    }
    
    return render(request, 'gamification/dashboard.html', context)

@login_required
def game_list(request):
    """Lista de juegos disponibles"""
    games = Juegos.objects.all()
    
    # Filtros
    game_type = request.GET.get('type')
    difficulty = request.GET.get('difficulty')
    
    if game_type:
        games = games.filter(IDtipoJuego_id=game_type)
    if difficulty:
        games = games.filter(NivelDificultad=difficulty)
    
    # Ordenamiento
    sort_by = request.GET.get('sort', 'IDjuego')
    if sort_by == 'popular':
        games = games.annotate(play_count=Count('juegousuario')).order_by('-play_count')
    elif sort_by == 'recent':
        games = games.order_by('-IDjuego')
    elif sort_by == 'difficulty':
        games = games.order_by('NivelDificultad')
    
    # Paginación
    paginator = Paginator(games, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'game_types': TipoJuego.objects.all(),
        'difficulties': [(1, 'Fácil'), (2, 'Básico'), (3, 'Intermedio'), (4, 'Avanzado'), (5, 'Experto')],
    }
    
    return render(request, 'gamification/game_list.html', context)

# ============================================================================
# VISTAS DE GESTIÓN DE AULAS (DOCENTES)
# ============================================================================

@login_required
def aula_create(request):
    """Crear una nueva aula virtual"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden crear aulas.')
        return redirect('gamification:dashboard')
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        codigo = request.POST.get('codigo')
        institucion_id = request.POST.get('institucion_id', 1)  # Por defecto
        
        # Generar código único si no se proporciona
        if not codigo:
            import uuid
            codigo = str(uuid.uuid4())[:8].upper()
        
        aula = Aulas.objects.create(
            NombreAula=nombre,
            CodigoAula=codigo,
            IDinstitucion=institucion_id,
            IDdocente=request.user
        )
        
        messages.success(request, f'Aula "{nombre}" creada exitosamente con código: {codigo}')
        return redirect('gamification:aula_detail', aula_id=aula.IDaula)
    
    return render(request, 'gamification/aula_create.html')

@login_required
def aula_list(request):
    """Lista de aulas del docente"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden ver esta página.')
        return redirect('gamification:dashboard')
    
    aulas = Aulas.objects.filter(IDdocente=request.user).order_by('-FechaCreacion')
    
    context = {
        'aulas': aulas,
    }
    
    return render(request, 'gamification/aula_list.html', context)

@login_required
def aula_detail(request, aula_id):
    """Detalle de un aula con estudiantes y actividades"""
    aula = get_object_or_404(Aulas, IDaula=aula_id, IDdocente=request.user)
    
    # Estudiantes del aula
    estudiantes = AulaEstudiante.objects.filter(IDaula=aula)
    
    # Actividades del aula
    actividades = Actividades.objects.filter(IDaula=aula).order_by('-IDactividad')
    
    # Rankings del aula
    rankings = Ranking.objects.filter(IDaula=aula).order_by('-puntos_totales')[:10]
    
    context = {
        'aula': aula,
        'estudiantes': estudiantes,
        'actividades': actividades,
        'rankings': rankings,
    }
    
    return render(request, 'gamification/aula_detail.html', context)

# ============================================================================
# VISTAS DE ACTIVIDADES
# ============================================================================

@login_required
def actividad_create(request, aula_id):
    """Crear una nueva actividad para un aula"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden crear actividades.')
        return redirect('gamification:dashboard')
    
    aula = get_object_or_404(Aulas, IDaula=aula_id, IDdocente=request.user)
    
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        instrucciones = request.POST.get('instrucciones')
        tipo_actividad_id = request.POST.get('tipo_actividad')
        ficha_id = request.POST.get('ficha_id', 1)  # Por defecto
        
        actividad = Actividades.objects.create(
            Titulo=titulo,
            Instrucciones=instrucciones,
            IDtipoActividad_id=tipo_actividad_id,
            IDficha=ficha_id,
            IDaula=aula
        )
        
        messages.success(request, f'Actividad "{titulo}" creada exitosamente.')
        return redirect('gamification:aula_detail', aula_id=aula.IDaula)
    
    context = {
        'aula': aula,
        'tipos_actividad': TipoActividad.objects.all(),
    }
    
    return render(request, 'gamification/actividad_create.html', context)

@login_required
def actividad_detail(request, actividad_id):
    """Detalle de una actividad con progreso de estudiantes"""
    actividad = get_object_or_404(Actividades, IDactividad=actividad_id)
    
    # Verificar que el usuario tenga acceso a esta actividad
    if request.user.user_type == 1:  # Estudiante
        if not AulaEstudiante.objects.filter(IDestudiante=request.user, IDaula=actividad.IDaula).exists():
            messages.error(request, 'No tienes acceso a esta actividad.')
            return redirect('gamification:dashboard')
    elif request.user.user_type == 2:  # Docente
        if actividad.IDaula.IDdocente != request.user:
            messages.error(request, 'No tienes acceso a esta actividad.')
            return redirect('gamification:dashboard')
    
    # Progreso de estudiantes en esta actividad
    progresos = Progreso.objects.filter(IDactividad=actividad).order_by('-Fecha')
    
    context = {
        'actividad': actividad,
        'progresos': progresos,
    }
    
    return render(request, 'gamification/actividad_detail.html', context)

# ============================================================================
# VISTAS DE DESAFÍOS
# ============================================================================

@login_required
def desafios_list(request):
    """Lista de desafíos disponibles para el usuario"""
    user = request.user
    nivel, created = Niveles.objects.get_or_create(IDusuario=user)
    
    # Desafíos disponibles según el nivel del usuario
    desafios_disponibles = Desafios.objects.filter(
        activo=True,
        nivel_minimo__lte=nivel.nivel,
        fecha_inicio__lte=timezone.now(),
        fecha_fin__gte=timezone.now()
    )
    
    # Progreso del usuario en desafíos
    progreso_desafios = DesafiosUsuario.objects.filter(IDusuario=user)
    
    context = {
        'desafios_disponibles': desafios_disponibles,
        'progreso_desafios': progreso_desafios,
        'user_level': nivel.nivel,
    }
    
    return render(request, 'gamification/desafios_list.html', context)

@login_required
def desafio_detail(request, desafio_id):
    """Detalle de un desafío específico"""
    desafio = get_object_or_404(Desafios, IDdesafio=desafio_id, activo=True)
    user = request.user
    
    # Verificar si el usuario puede acceder al desafío
    nivel, created = Niveles.objects.get_or_create(IDusuario=user)
    if nivel.nivel < desafio.nivel_minimo:
        messages.error(request, f'Necesitas nivel {desafio.nivel_minimo} para acceder a este desafío.')
        return redirect('gamification:desafios_list')
    
    # Progreso del usuario en este desafío
    progreso, created = DesafiosUsuario.objects.get_or_create(
        IDusuario=user,
        IDdesafio=desafio
    )
    
    context = {
        'desafio': desafio,
        'progreso': progreso,
        'user_level': nivel.nivel,
    }
    
    return render(request, 'gamification/desafio_detail.html', context)

# ============================================================================
# VISTAS DE RANKINGS Y ESTADÍSTICAS
# ============================================================================

@login_required
def rankings_list(request):
    """Lista de rankings por aula"""
    user = request.user
    
    if user.user_type == 2:  # Docente
        # Rankings de las aulas del docente
        aulas = Aulas.objects.filter(IDdocente=user)
        rankings_por_aula = {}
        for aula in aulas:
            rankings_por_aula[aula] = Ranking.objects.filter(IDaula=aula).order_by('-puntos_totales')[:10]
    else:  # Estudiante
        # Rankings de las aulas donde está el estudiante
        aulas_estudiante = AulaEstudiante.objects.filter(IDestudiante=user)
        rankings_por_aula = {}
        for aula_est in aulas_estudiante:
            rankings_por_aula[aula_est.IDaula] = Ranking.objects.filter(IDaula=aula_est.IDaula).order_by('-puntos_totales')[:10]
    
    context = {
        'rankings_por_aula': rankings_por_aula,
    }
    
    return render(request, 'gamification/rankings_list.html', context)

@login_required
def estadisticas_personales(request):
    """Estadísticas personales del usuario"""
    user = request.user
    
    # Obtener nivel y estadísticas
    nivel, created = Niveles.objects.get_or_create(IDusuario=user)
    estadisticas, created = EstadisticasUsuario.objects.get_or_create(IDusuario=user)
    
    # Obtener insignias
    insignias = InsigniasUsuario.objects.filter(IDusuario=user)
    
    # Historial de actividades
    historial_actividades = Progreso.objects.filter(IDusuario=user).order_by('-Fecha')[:20]
    
    # Historial de juegos
    historial_juegos = JuegoUsuario.objects.filter(IDusuario=user).order_by('-FechaJugada')[:20]
    
    # Logs de gamificación
    logs = LogGamificacion.objects.filter(IDusuario=user).order_by('-fecha_evento')[:50]
    
    context = {
        'nivel': nivel,
        'estadisticas': estadisticas,
        'insignias': insignias,
        'historial_actividades': historial_actividades,
        'historial_juegos': historial_juegos,
        'logs': logs,
    }
    
    return render(request, 'gamification/estadisticas_personales.html', context)

# ============================================================================
# VISTAS DE JUEGOS
# ============================================================================

@login_required
def game_create(request):
    """Crear un nuevo juego"""
    if request.method == 'POST':
        # Lógica para crear juego
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        tipo_juego_id = request.POST.get('tipo_juego')
        nivel_dificultad = request.POST.get('nivel_dificultad')
        instrucciones = request.POST.get('instrucciones')
        
        juego = Juegos.objects.create(
            NombreJuego=nombre,
            Descripcion=descripcion,
            IDtipoJuego_id=tipo_juego_id,
            NivelDificultad=nivel_dificultad,
            Instrucciones=instrucciones
        )
        
        messages.success(request, f'Juego "{nombre}" creado exitosamente.')
        return redirect('gamification:game_edit', game_id=juego.IDjuego)
    
    context = {
        'game_types': TipoJuego.objects.all(),
        'difficulties': [(1, 'Fácil'), (2, 'Básico'), (3, 'Intermedio'), (4, 'Avanzado'), (5, 'Experto')],
    }
    
    return render(request, 'gamification/game_create.html', context)

@login_required
def game_edit(request, game_id):
    """Editar un juego existente"""
    game = get_object_or_404(Juegos, IDjuego=game_id)
    
    if request.method == 'POST':
        game.NombreJuego = request.POST.get('nombre')
        game.Descripcion = request.POST.get('descripcion')
        game.NivelDificultad = int(request.POST.get('nivel_dificultad', 1))
        game.Instrucciones = request.POST.get('instrucciones')
        
        game.save()
        messages.success(request, 'Juego actualizado exitosamente.')
        return redirect('gamification:game_edit', game_id=game.IDjuego)
    
    context = {
        'game': game,
        'difficulties': [(1, 'Fácil'), (2, 'Básico'), (3, 'Intermedio'), (4, 'Avanzado'), (5, 'Experto')],
        'game_types': TipoJuego.objects.all(),
    }
    
    return render(request, 'gamification/game_edit.html', context)

@login_required
def quiz_play(request, game_id):
    """Jugar un cuestionario"""
    game = get_object_or_404(Juegos, IDjuego=game_id)
    
    # Registrar juego del usuario
    juego_usuario = JuegoUsuario.objects.create(
        IDusuario=request.user,
        IDjuego=game,
        Puntaje=0
    )
        
    # Obtener nivel del usuario
    nivel, created = Niveles.objects.get_or_create(IDusuario=request.user)
    
    context = {
        'game': game,
        'user_level': nivel.nivel,
        'session_id': juego_usuario.id,
    }
    
    return render(request, 'gamification/quiz_play.html', context)

@login_required
def rapid_questions_play(request, game_id):
    """Jugar preguntas rápidas"""
    game = get_object_or_404(Juegos, IDjuego=game_id)
    
    # Registrar juego del usuario
    juego_usuario = JuegoUsuario.objects.create(
        IDusuario=request.user,
        IDjuego=game,
        Puntaje=0
    )
    
    context = {
        'game': game,
        'session_id': juego_usuario.id,
    }
    
    return render(request, 'gamification/rapid_questions_play.html', context)

@login_required
def leaderboard(request, game_id=None):
    """Tabla de clasificación"""
    if game_id:
        # Ranking específico de un juego
        rankings = Ranking.objects.filter(IDjuego_id=game_id).order_by('-puntos_totales')
        game = get_object_or_404(Juegos, IDjuego=game_id)
    else:
        # Ranking general
        rankings = Ranking.objects.all().order_by('-puntos_totales')
        game = None
    
    context = {
        'rankings': rankings[:50],  # Top 50
        'game': game,
    }
    
    return render(request, 'gamification/leaderboard.html', context)

@login_required
def user_profile(request, username=None):
    """Perfil de usuario con estadísticas"""
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
    
    # Obtener nivel y estadísticas
    nivel, created = Niveles.objects.get_or_create(IDusuario=user)
    estadisticas, created = EstadisticasUsuario.objects.get_or_create(IDusuario=user)
    
    # Obtener insignias
    insignias = InsigniasUsuario.objects.filter(IDusuario=user)
    
    # Obtener historial de juegos
    historial_juegos = JuegoUsuario.objects.filter(IDusuario=user).order_by('-FechaJugada')[:10]
    
    # Obtener progreso en actividades
    progreso_actividades = Progreso.objects.filter(IDusuario=user).order_by('-Fecha')[:10]
    
    # Obtener desafíos completados
    desafios_completados = DesafiosUsuario.objects.filter(
        IDusuario=user, 
        completado=True
    ).order_by('-fecha_completado')[:5]
    
    context = {
        'profile_user': user,
        'nivel': nivel,
        'estadisticas': estadisticas,
        'insignias': insignias,
        'historial_juegos': historial_juegos,
        'progreso_actividades': progreso_actividades,
        'desafios_completados': desafios_completados,
    }
    
    return render(request, 'gamification/user_profile.html', context)

# ============================================================================
# APIs
# ============================================================================

@csrf_exempt
def api_question_data(request, game_id):
    """API para obtener datos de preguntas de un juego"""
    if request.method == 'GET':
        game = get_object_or_404(Juegos, IDjuego=game_id)
        
        # Aquí deberías implementar la lógica para obtener preguntas
        # Por ahora retornamos datos de ejemplo
        questions_data = {
            'game_id': game_id,
            'game_name': game.NombreJuego,
            'questions': [
                {
                    'id': 1,
                    'question': '¿Cuál es la capital de Perú?',
                    'options': ['Lima', 'Arequipa', 'Trujillo', 'Cusco'],
                    'correct_answer': 0
                }
                ]
        }
        
        return JsonResponse(questions_data)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
def api_submit_answer(request, session_id):
    """API para enviar respuestas"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            answer = data.get('answer')
            question_id = data.get('question_id')
            # Aquí implementarías la lógica para procesar la respuesta
            # Por ahora solo registramos que se envió una respuesta
            # Actualizar puntuación del usuario
            user = request.user
            nivel, created = Niveles.objects.get_or_create(IDusuario=user)
            nivel.puntos_acumulados += 10  # Puntos por respuesta
            nivel.actualizar_nivel()
            nivel.save()
            # Registrar log
            LogGamificacion.objects.create(
                IDusuario=user,
                tipo_evento='respuesta_correcta',
                descripcion=f'Respuesta correcta en pregunta {question_id}',
                puntos_ganados=10
            )
            return JsonResponse({
                'success': True,
                'points_earned': 10,
                'new_total_points': nivel.puntos_acumulados,
                'new_level': nivel.nivel
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def notifications_list(request):
    """Lista de notificaciones del usuario"""
    # Por ahora retornamos una lista vacía
    # Aquí implementarías la lógica para obtener notificaciones reales
    notifications = []
    
    context = {
        'notifications': notifications,
    }
    
    return render(request, 'gamification/notifications_list.html', context)

@login_required
def notifications_count(request):
    """API para obtener el conteo de notificaciones no leídas"""
    from django.http import JsonResponse
    
    # Por ahora retornamos 0 notificaciones
    # Aquí implementarías la lógica para contar notificaciones reales
    count = 0
    
    return JsonResponse({'count': count})

@login_required
def notifications_ajax(request):
    """API para obtener notificaciones en formato AJAX"""
    from django.http import JsonResponse
    
    # Por ahora retornamos una lista vacía
    # Aquí implementarías la lógica para obtener notificaciones reales
    notifications = []
    
    return JsonResponse({'notifications': notifications})

# ============================================================================
# VISTAS DE TESTS Y CUESTIONARIOS
# ============================================================================

@login_required
def test_list(request, aula_id):
    """Lista de tests de un aula"""
    aula = get_object_or_404(Aulas, IDaula=aula_id)
    
    # Verificar permisos
    if request.user.user_type == 2:  # Docente
        if aula.IDdocente != request.user:
            messages.error(request, 'No tienes permisos para ver esta aula.')
            return redirect('gamification:dashboard')
        tests = Test.objects.filter(IDaula=aula).order_by('-fecha_creacion')
    else:  # Estudiante
        if not AulaEstudiante.objects.filter(IDaula=aula, IDestudiante=request.user).exists():
            messages.error(request, 'No tienes acceso a esta aula.')
            return redirect('gamification:dashboard')
        tests = Test.objects.filter(IDaula=aula, activo=True).order_by('-fecha_creacion')
    
    context = {
        'aula': aula,
        'tests': tests,
    }
    
    return render(request, 'gamification/test_list.html', context)

@login_required
def test_public_list(request):
    """Lista de tests públicos disponibles para copiar"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden ver tests públicos.')
        return redirect('gamification:dashboard')
    
    # Obtener tests públicos de otros docentes
    tests_publicos = Test.objects.filter(
        es_publico=True,
        IDdocente__user_type=2  # Solo de docentes
    ).exclude(IDdocente=request.user).order_by('-fecha_creacion')
    
    # Obtener aulas del docente
    aulas_docente = Aulas.objects.filter(IDdocente=request.user)
    
    # Calcular número de docentes activos
    docentes_activos = tests_publicos.values('IDdocente').distinct().count()
    
    context = {
        'tests_publicos': tests_publicos,
        'aulas_docente': aulas_docente,
        'docentes_activos': docentes_activos,
    }
    
    return render(request, 'gamification/test_public_list.html', context)

@login_required
def test_copy(request, test_id):
    """Copiar un test público a una aula del docente"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden copiar tests.')
        return redirect('gamification:dashboard')
    
    test_original = get_object_or_404(Test, IDtest=test_id, es_publico=True)
    aula_destino_id = request.POST.get('aula_destino')
    
    if not aula_destino_id:
        messages.error(request, 'Debes seleccionar una aula de destino.')
        return redirect('gamification:test_public_list')
    
    aula_destino = get_object_or_404(Aulas, IDaula=aula_destino_id, IDdocente=request.user)
    
    try:
        nuevo_test = test_original.copiar_test(request.user, aula_destino)
        messages.success(request, f'Test "{test_original.titulo}" copiado exitosamente a {aula_destino.NombreAula}.')
        return redirect('gamification:test_edit', test_id=nuevo_test.IDtest)
    except Exception as e:
        messages.error(request, f'Error al copiar el test: {str(e)}')
        return redirect('gamification:test_public_list')

@login_required
def test_make_public(request, test_id):
    """Hacer público un test para que otros docentes puedan copiarlo"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden hacer públicos los tests.')
        return redirect('gamification:dashboard')
    
    test = get_object_or_404(Test, IDtest=test_id, IDdocente=request.user)
    
    if request.method == 'POST':
        test.es_publico = True
        test.save()
        messages.success(request, f'Test "{test.titulo}" ahora es público y otros docentes pueden copiarlo.')
        return redirect('gamification:test_detail', test_id=test.IDtest)
    
    return redirect('gamification:test_detail', test_id=test.IDtest)

@login_required
def test_create(request, aula_id):
    """Crear un nuevo test para un aula con preguntas incluidas"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden crear tests.')
        return redirect('gamification:dashboard')
    
    aula = get_object_or_404(Aulas, IDaula=aula_id, IDdocente=request.user)
    
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        tiempo_limite = request.POST.get('tiempo_limite', 30)
        puntos_por_pregunta = request.POST.get('puntos_por_pregunta', 10)
        es_publico = request.POST.get('es_publico') == 'on'
        
        try:
            from django.utils.dateparse import parse_datetime
            fecha_inicio = parse_datetime(fecha_inicio)
            fecha_fin = parse_datetime(fecha_fin)
            
            preguntas_data = request.POST.getlist('preguntas[]')
            tipos_pregunta = request.POST.getlist('tipos_pregunta[]')
            puntos_preguntas = request.POST.getlist('puntos_pregunta[]')
            preguntas_validas = [p for p in preguntas_data if p.strip()]
            if not preguntas_validas:
                messages.error(request, 'Debes agregar al menos una pregunta válida al test.')
                return render(request, 'gamification/test_create.html', {'aula': aula})
            
            test = Test.objects.create(
                titulo=titulo,
                descripcion=descripcion,
                IDaula=aula,
                IDdocente=request.user,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                tiempo_limite=int(tiempo_limite),
                puntos_por_pregunta=int(puntos_por_pregunta),
                es_publico=es_publico
            )
            
            # Procesar preguntas del formulario
            for i, (pregunta_texto, tipo_pregunta, puntos) in enumerate(zip(preguntas_data, tipos_pregunta, puntos_preguntas)):
                if pregunta_texto.strip():  # Solo crear preguntas no vacías
                    pregunta = Pregunta.objects.create(
                        IDtest=test,
                        pregunta=pregunta_texto,
                        tipo_pregunta=tipo_pregunta,
                        puntos=int(puntos),
                        orden=i+1
                    )
                    # Si es opción múltiple, crear las opciones
                    if tipo_pregunta == 'opcion_multiple':
                        opciones = request.POST.getlist(f'opciones_{i}[]')
                        correcta = request.POST.get(f'correcta_{i}')
                        for j, opcion_texto in enumerate(opciones):
                            if opcion_texto.strip():
                                Opcion.objects.create(
                                    IDpregunta=pregunta,
                                    texto=opcion_texto,
                                    es_correcta=str(j) == correcta,
                                    orden=j+1
                                )
            messages.success(request, f'Test "{titulo}" creado exitosamente con {test.pregunta_set.count()} preguntas.')
            return redirect('gamification:test_list', aula_id=aula.IDaula)
        except Exception as e:
            messages.error(request, f'Error al crear el test: {str(e)}')
    context = {
        'aula': aula,
    }
    return render(request, 'gamification/test_create.html', context)

@login_required
def test_detail(request, test_id):
    """Detalle de un test con sus preguntas"""
    test = get_object_or_404(Test, IDtest=test_id)
    
    # Verificar permisos
    if request.user.user_type == 2:  # Docente
        if test.IDdocente != request.user:
            messages.error(request, 'No tienes permisos para ver este test.')
            return redirect('gamification:dashboard')
    else:  # Estudiante
        if not AulaEstudiante.objects.filter(IDaula=test.IDaula, IDestudiante=request.user).exists():
            messages.error(request, 'No tienes acceso a este test.')
            return redirect('gamification:dashboard')
    
    preguntas = Pregunta.objects.filter(IDtest=test).order_by('orden')
    
    # Si es estudiante, verificar si ya completó el test
    resultado_estudiante = None
    if request.user.user_type == 1:  # Estudiante
        resultado_estudiante = ResultadoTest.objects.filter(
            IDtest=test,
            IDestudiante=request.user
        ).first()
    
    context = {
        'test': test,
        'preguntas': preguntas,
        'resultado_estudiante': resultado_estudiante,
    }
    
    return render(request, 'gamification/test_detail.html', context)

@login_required
def test_edit(request, test_id):
    """Editar un test existente"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden editar tests.')
        return redirect('gamification:dashboard')
    
    test = get_object_or_404(Test, IDtest=test_id, IDdocente=request.user)
    
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        tiempo_limite = request.POST.get('tiempo_limite')
        puntos_por_pregunta = request.POST.get('puntos_por_pregunta')
        activo = request.POST.get('activo') == 'on'
        
        try:
            from django.utils.dateparse import parse_datetime
            fecha_inicio = parse_datetime(fecha_inicio)
            fecha_fin = parse_datetime(fecha_fin)
            
            test.titulo = titulo
            test.descripcion = descripcion
            test.fecha_inicio = fecha_inicio
            test.fecha_fin = fecha_fin
            test.tiempo_limite = int(tiempo_limite)
            test.puntos_por_pregunta = int(puntos_por_pregunta)
            test.activo = activo
            test.save()
            
            messages.success(request, f'Test "{titulo}" actualizado exitosamente.')
            return redirect('gamification:test_detail', test_id=test.IDtest)
            
        except Exception as e:
            messages.error(request, f'Error al actualizar el test: {str(e)}')
    
    context = {
        'test': test,
        'max_score': test.pregunta_set.count() * test.puntos_por_pregunta,
    }
    
    return render(request, 'gamification/test_edit.html', context)

@login_required
def pregunta_create(request, test_id):
    """Crear una nueva pregunta para un test"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden crear preguntas.')
        return redirect('gamification:dashboard')
    
    test = get_object_or_404(Test, IDtest=test_id, IDdocente=request.user)
    
    if request.method == 'POST':
        pregunta_texto = request.POST.get('pregunta')
        tipo_pregunta = request.POST.get('tipo_pregunta')
        puntos = request.POST.get('puntos', 10)
        orden = request.POST.get('orden', 1)
        
        try:
            pregunta = Pregunta.objects.create(
                IDtest=test,
                pregunta=pregunta_texto,
                tipo_pregunta=tipo_pregunta,
                puntos=int(puntos),
                orden=int(orden)
            )
            
            # Si es opción múltiple, crear las opciones
            if tipo_pregunta == 'opcion_multiple':
                opciones = request.POST.getlist('opciones[]')
                correcta = request.POST.get('correcta')
                
                for i, opcion_texto in enumerate(opciones):
                    if opcion_texto.strip():  # Solo crear opciones no vacías
                        Opcion.objects.create(
                            IDpregunta=pregunta,
                            texto=opcion_texto,
                            es_correcta=str(i) == correcta,
                            orden=i+1
                        )
            
            messages.success(request, 'Pregunta creada exitosamente.')
            return redirect('gamification:test_detail', test_id=test.IDtest)
            
        except Exception as e:
            messages.error(request, f'Error al crear la pregunta: {str(e)}')
    
    context = {
        'test': test,
    }
    
    return render(request, 'gamification/pregunta_create.html', context)

@login_required
def test_take(request, test_id):
    """Tomar un test como estudiante"""
    if request.user.user_type != 1:  # Solo estudiantes
        messages.error(request, 'Solo los estudiantes pueden tomar tests.')
        return redirect('gamification:dashboard')
    
    test = get_object_or_404(Test, IDtest=test_id, activo=True)
    
    # Verificar que el estudiante está inscrito en el aula
    if not AulaEstudiante.objects.filter(IDaula=test.IDaula, IDestudiante=request.user).exists():
        messages.error(request, 'No tienes acceso a este test.')
        return redirect('gamification:dashboard')
    
    # Verificar fechas del test
    now = timezone.now()
    if now < test.fecha_inicio or now > test.fecha_fin:
        messages.error(request, 'Este test no está disponible en este momento.')
        return redirect('gamification:test_detail', test_id=test.IDtest)
    
    # Verificar si ya completó el test
    resultado_existente = ResultadoTest.objects.filter(
        IDtest=test,
        IDestudiante=request.user,
        completado=True
    ).first()
    
    if resultado_existente:
        messages.warning(request, 'Ya completaste este test.')
        return redirect('gamification:test_detail', test_id=test.IDtest)
    
    # Obtener preguntas del test
    preguntas = Pregunta.objects.filter(IDtest=test).order_by('orden')
    
    if request.method == 'POST':
        # Procesar respuestas del estudiante
        puntuacion_total = 0
        preguntas_correctas = 0
        total_preguntas = preguntas.count()
        
        for pregunta in preguntas:
            if pregunta.tipo_pregunta == 'opcion_multiple':
                opcion_id = request.POST.get(f'pregunta_{pregunta.IDpregunta}')
                if opcion_id:
                    opcion = Opcion.objects.get(IDopcion=opcion_id)
                    es_correcta = opcion.es_correcta
                    puntos_obtenidos = pregunta.puntos if es_correcta else 0
                    
                    RespuestaEstudiante.objects.create(
                        IDtest=test,
                        IDpregunta=pregunta,
                        IDestudiante=request.user,
                        IDopcion_seleccionada=opcion,
                        es_correcta=es_correcta,
                        puntos_obtenidos=puntos_obtenidos
                    )
                    
                    if es_correcta:
                        preguntas_correctas += 1
                        puntuacion_total += puntos_obtenidos
            
            elif pregunta.tipo_pregunta == 'verdadero_falso':
                respuesta = request.POST.get(f'pregunta_{pregunta.IDpregunta}')
                if respuesta:
                    # Aquí implementarías la lógica para verdadero/falso
                    pass
            
            elif pregunta.tipo_pregunta == 'texto_corto':
                respuesta_texto = request.POST.get(f'pregunta_{pregunta.IDpregunta}')
                if respuesta_texto:
                    RespuestaEstudiante.objects.create(
                        IDtest=test,
                        IDpregunta=pregunta,
                        IDestudiante=request.user,
                        respuesta_texto=respuesta_texto,
                        puntos_obtenidos=0  # Requiere revisión manual
                    )
        
        # Crear resultado del test
        porcentaje_acierto = (preguntas_correctas / total_preguntas * 100) if total_preguntas > 0 else 0
        
        ResultadoTest.objects.create(
            IDtest=test,
            IDestudiante=request.user,
            puntuacion_total=puntuacion_total,
            puntuacion_maxima=total_preguntas * test.puntos_por_pregunta,
            porcentaje_acierto=porcentaje_acierto,
            preguntas_correctas=preguntas_correctas,
            total_preguntas=total_preguntas,
            fecha_inicio=now,
            fecha_fin=now,
            completado=True
        )
        
        # Actualizar nivel del estudiante
        nivel, created = Niveles.objects.get_or_create(IDusuario=request.user)
        nivel.puntos_acumulados += puntuacion_total
        nivel.actualizar_nivel()
        nivel.save()
        
        messages.success(request, f'Test completado. Puntuación: {puntuacion_total} puntos.')
        return redirect('gamification:test_results', test_id=test.IDtest)
    
    context = {
        'test': test,
        'preguntas': preguntas,
    }
    
    return render(request, 'gamification/test_take.html', context)

@login_required
def test_results(request, test_id):
    """Ver resultados de un test"""
    test = get_object_or_404(Test, IDtest=test_id)
    
    # Verificar permisos
    if request.user.user_type == 1:  # Estudiante
        if not test.activo:
            messages.error(request, 'Este test no está disponible.')
            return redirect('gamification:dashboard')
        # Solo mostrar su propio resultado
        resultados = ResultadoTest.objects.filter(IDtest=test, IDestudiante=request.user)
    else:  # Docente
        if test.IDdocente != request.user:
            messages.error(request, 'No tienes permisos para ver estos resultados.')
            return redirect('gamification:dashboard')
        # Mostrar todos los resultados
        resultados = ResultadoTest.objects.filter(IDtest=test).order_by('-fecha_fin')
    
    context = {
        'test': test,
        'resultados': resultados,
    }
    
    return render(request, 'gamification/test_results.html', context)

@login_required
def test_delete(request, test_id):
    """Eliminar un test"""
    test = get_object_or_404(Test, IDtest=test_id, IDdocente=request.user)
    
    if request.method == 'POST':
        titulo = test.titulo
        test.delete()
        messages.success(request, f'Test "{titulo}" eliminado exitosamente.')
        return redirect('users:dashboard_teacher')
    
    context = {
        'test': test,
    }
    
    return render(request, 'gamification/test_confirm_delete.html', context)

@login_required
def test_results_detail(request, resultado_id):
    """Ver detalle de un resultado específico"""
    resultado = get_object_or_404(ResultadoTest, IDresultado=resultado_id)
    
    # Verificar permisos
    if request.user.user_type == 1:  # Estudiante
        if resultado.IDestudiante != request.user:
            messages.error(request, 'No tienes permisos para ver este resultado.')
            return redirect('gamification:dashboard')
    else:  # Docente
        if resultado.IDtest.IDdocente != request.user:
            messages.error(request, 'No tienes permisos para ver este resultado.')
            return redirect('gamification:dashboard')
    
    # Obtener respuestas detalladas
    respuestas = RespuestaEstudiante.objects.filter(IDresultado=resultado)
    
    context = {
        'resultado': resultado,
        'respuestas': respuestas,
    }
    
    return render(request, 'gamification/test_results_detail.html', context)

@login_required
def test_export_results(request, test_id):
    """Exportar resultados de un test"""
    test = get_object_or_404(Test, IDtest=test_id, IDdocente=request.user)
    
    if request.method == 'POST':
        formato = request.POST.get('formato', 'csv')
        
        resultados = ResultadoTest.objects.filter(IDtest=test).order_by('-fecha_fin')
        
        if formato == 'csv':
            import csv
            from django.http import HttpResponse
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="resultados_{test.titulo}.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Estudiante', 'Puntuación', 'Porcentaje', 'Preguntas Correctas', 'Tiempo Empleado', 'Fecha'])
            
            for resultado in resultados:
                writer.writerow([
                    resultado.IDestudiante.username,
                    resultado.puntuacion_total,
                    f"{resultado.porcentaje_acierto:.1f}%",
                    resultado.preguntas_correctas,
                    f"{resultado.tiempo_empleado}s",
                    resultado.fecha_fin.strftime("%d/%m/%Y %H:%M")
                ])
            
            return response
        else:
            messages.error(request, 'Formato no soportado.')
    
    context = {
        'test': test,
    }
    
    return render(request, 'gamification/test_export.html', context)

@login_required
def test_duplicate(request, test_id):
    """Duplicar un test"""
    test = get_object_or_404(Test, IDtest=test_id)
    
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden duplicar tests.')
        return redirect('gamification:dashboard')
    
    if request.method == 'POST':
        aula_id = request.POST.get('aula_destino')
        if not aula_id:
            messages.error(request, 'Debes seleccionar un aula de destino.')
            return redirect('gamification:test_detail', test_id=test_id)
        
        try:
            aula = Aulas.objects.get(IDaula=aula_id, IDdocente=request.user)
        except Aulas.DoesNotExist:
            messages.error(request, 'Aula no válida.')
            return redirect('gamification:test_detail', test_id=test_id)
        
        # Crear copia del test
        nuevo_test = Test.objects.create(
            titulo=f"{test.titulo} (Copia)",
            descripcion=test.descripcion,
            tiempo_limite=test.tiempo_limite,
            puntos_por_pregunta=test.puntos_por_pregunta,
            fecha_inicio=timezone.now(),
            fecha_fin=timezone.now() + timezone.timedelta(days=30),
            IDaula=aula,
            IDdocente=request.user,
            activo=False,  # Inactivo por defecto
            es_publico=False,
            es_copia=True
        )
        
        # Copiar preguntas
        for pregunta in test.pregunta_set.all():
            nueva_pregunta = Pregunta.objects.create(
                pregunta=pregunta.pregunta,
                tipo_pregunta=pregunta.tipo_pregunta,
                puntos=pregunta.puntos,
                orden=pregunta.orden,
                IDtest=nuevo_test
            )
            
            # Copiar opciones si es de opción múltiple
            if pregunta.tipo_pregunta == 'opcion_multiple':
                for opcion in pregunta.opcion_set.all():
                    Opcion.objects.create(
                        texto=opcion.texto,
                        es_correcta=opcion.es_correcta,
                        IDpregunta=nueva_pregunta
                    )
        
        messages.success(request, f'Test duplicado exitosamente en "{aula.NombreAula}"')
        return redirect('gamification:test_detail', test_id=nuevo_test.IDtest)
    
    # Obtener aulas del docente
    aulas_docente = Aulas.objects.filter(IDdocente=request.user)
    
    context = {
        'test': test,
        'aulas_docente': aulas_docente,
    }
    
    return render(request, 'gamification/test_duplicate.html', context)

# ============================================================================
# VISTAS DE JUEGOS EDUCATIVOS
# ============================================================================

@login_required
def game_memory(request):
    """Juego de memoria de especies"""
    user = request.user
    
    # Obtener estadísticas del usuario para este juego
    game_stats, created = EstadisticasUsuario.objects.get_or_create(IDusuario=user)
    
    # Obtener progreso del usuario
    progreso, created = Progreso.objects.get_or_create(IDusuario=user)
    
    context = {
        'user': user,
        'game_stats': game_stats,
        'progreso': progreso,
    }
    
    return render(request, 'gamification/game_memory.html', context)

@login_required
def game_crossword(request):
    """Juego de crucigrama ecológico"""
    user = request.user
    
    # Obtener estadísticas del usuario para este juego
    game_stats, created = EstadisticasUsuario.objects.get_or_create(IDusuario=user)
    
    # Obtener progreso del usuario
    progreso, created = Progreso.objects.get_or_create(IDusuario=user)
    
    context = {
        'user': user,
        'game_stats': game_stats,
        'progreso': progreso,
    }
    
    return render(request, 'gamification/game_crossword.html', context)

@login_required
def game_classification(request):
    """Juego de clasificación de ecosistemas"""
    user = request.user
    
    # Obtener estadísticas del usuario para este juego
    game_stats, created = EstadisticasUsuario.objects.get_or_create(IDusuario=user)
    
    # Obtener progreso del usuario
    progreso, created = Progreso.objects.get_or_create(IDusuario=user)
    
    context = {
        'user': user,
        'game_stats': game_stats,
        'progreso': progreso,
    }
    
    return render(request, 'gamification/game_classification.html', context)

@login_required
def game_quiz_ecosystem(request):
    """Quiz sobre ecosistemas"""
    user = request.user
    
    # Obtener estadísticas del usuario para este juego
    game_stats, created = EstadisticasUsuario.objects.get_or_create(IDusuario=user)
    
    # Obtener progreso del usuario
    progreso, created = Progreso.objects.get_or_create(IDusuario=user)
    
    context = {
        'user': user,
        'game_stats': game_stats,
        'progreso': progreso,
    }
    
    return render(request, 'gamification/game_quiz_ecosystem.html', context)

@login_required
def game_food_chain(request):
    """Juego de cadena alimenticia"""
    user = request.user
    
    # Obtener estadísticas del usuario para este juego
    game_stats, created = EstadisticasUsuario.objects.get_or_create(IDusuario=user)
    
    # Obtener progreso del usuario
    progreso, created = Progreso.objects.get_or_create(IDusuario=user)
    
    context = {
        'user': user,
        'game_stats': game_stats,
        'progreso': progreso,
    }
    
    return render(request, 'gamification/game_food_chain.html', context)

# ============================================================================
# APIs PARA JUEGOS
# ============================================================================

@csrf_exempt
def api_game_complete(request):
    """API para registrar completación de juego"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = request.user
            game_type = data.get('game_type')
            score = data.get('score', 0)
            time_taken = data.get('time_taken', 0)
            moves = data.get('moves', 0)
            
            # Actualizar estadísticas del usuario
            estadisticas, created = EstadisticasUsuario.objects.get_or_create(IDusuario=user)
            estadisticas.juegos_jugados += 1
            estadisticas.puntos_totales += score
            estadisticas.tiempo_total_jugado += time_taken
            estadisticas.save()
            
            # Actualizar progreso del usuario
            progreso, created = Progreso.objects.get_or_create(IDusuario=user)
            progreso.puntos_actuales += score
            progreso.save()
            
            # Registrar sesión de juego
            JuegoUsuario.objects.create(
                IDusuario=user,
                IDjuego=Juegos.objects.get_or_create(
                    NombreJuego=f"{game_type} Game",
                    defaults={'Descripcion': f'Juego de {game_type}', 'NivelDificultad': 2}
                )[0],
                Puntuacion=score,
                TiempoJugado=time_taken,
                FechaJugada=timezone.now()
            )
            
            # Verificar si sube de nivel
            nivel, created = Niveles.objects.get_or_create(IDusuario=user)
            puntos_para_siguiente = nivel.nivel * 100
            
            if progreso.puntos_actuales >= puntos_para_siguiente:
                nivel.nivel += 1
                nivel.puntos_acumulados += progreso.puntos_actuales
                progreso.puntos_actuales = 0
                nivel.save()
                progreso.save()
                
                return JsonResponse({
                    'success': True,
                    'level_up': True,
                    'new_level': nivel.nivel,
                    'message': f'¡Felicidades! Has subido al nivel {nivel.nivel}'
                })
            
            return JsonResponse({
                'success': True,
                'level_up': False,
                'score': score,
                'total_points': estadisticas.puntos_totales
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@csrf_exempt
def api_get_game_stats(request):
    """API para obtener estadísticas de juegos del usuario"""
    user = request.user
    
    estadisticas, created = EstadisticasUsuario.objects.get_or_create(IDusuario=user)
    progreso, created = Progreso.objects.get_or_create(IDusuario=user)
    nivel, created = Niveles.objects.get_or_create(IDusuario=user)
    
    return JsonResponse({
        'total_games': estadisticas.juegos_jugados,
        'total_points': estadisticas.puntos_totales,
        'current_level': nivel.nivel,
        'current_points': progreso.puntos_actuales,
        'points_to_next': (nivel.nivel * 100) - progreso.puntos_actuales
    })

