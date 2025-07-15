from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum, Max, Min
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import (
    Test, Pregunta, Opcion, RespuestaEstudiante, ResultadoTest,
    Classroom, ClassroomStudent, Notification
)
from apps.users.models import User

from .models import (
    Juegos, JuegoUsuario, Progreso, Niveles, Insignias, InsigniasUsuario,
    Activities, ActivityType, GameType,
    Desafios, DesafiosUsuario, Ranking, RecompensasUsuario,
    EstadisticasUsuario, LogGamificacion
)
from apps.animals.models import Animal
from apps.plants.models import Plant
from apps.common.models import Category, Location

from django.contrib.auth import get_user_model
from .utils import (
    asignar_puntuacion_actividad, 
    obtener_estadisticas_usuario,
    crear_nivel_usuario,
    asignar_puntuacion_perfecta
)

User = get_user_model()

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
    for aula_estudiante in ClassroomStudent.objects.filter(student=user):
        actividades_asignadas.extend(Activities.objects.filter(IDaula=aula_estudiante.classroom))
    
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
        'game_types': GameType.objects.all(),
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
        
        aula = Classroom.objects.create(
            name=nombre,
            code=codigo,
            teacher=request.user,
            created_at=timezone.now()
        )
        
        messages.success(request, f'Aula "{nombre}" creada exitosamente con código: {codigo}')
        return redirect('gamification:aula_detail', aula_id=aula.id)
    
    return render(request, 'gamification/aula_create.html')

@login_required
def aula_list(request):
    """Lista de aulas del docente"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden ver esta página.')
        return redirect('gamification:dashboard')
    
    aulas = Classroom.objects.filter(teacher=request.user).order_by('-created_at')
    
    context = {
        'aulas': aulas,
    }
    
    return render(request, 'gamification/aula_list.html', context)

@login_required
def aula_detail(request, aula_id):
    """Detalle de un aula con estudiantes y actividades"""
    aula = get_object_or_404(Classroom, id=aula_id, teacher=request.user)
    
    # Estudiantes del aula
    estudiantes = ClassroomStudent.objects.filter(classroom=aula)
    
    # Actividades del aula
    actividades = Activities.objects.filter(IDaula=aula).order_by('-IDactividad')
    
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
    
    aula = get_object_or_404(Classroom, IDaula=aula_id, IDdocente=request.user)
    
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        instrucciones = request.POST.get('instrucciones')
        tipo_actividad_id = request.POST.get('tipo_actividad')
        ficha_id = request.POST.get('ficha_id', 1)  # Por defecto
        
        actividad = Activities.objects.create(
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
        'tipos_actividad': ActivityType.objects.all(),
    }
    
    return render(request, 'gamification/actividad_create.html', context)

@login_required
def actividad_detail(request, actividad_id):
    """Detalle de una actividad con progreso de estudiantes"""
    actividad = get_object_or_404(Activities, IDactividad=actividad_id)
    
    # Verificar que el usuario tenga acceso a esta actividad
    if request.user.user_type == 1:  # Estudiante
        if not ClassroomStudent.objects.filter(IDestudiante=request.user, IDaula=actividad.IDaula).exists():
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
        aulas = Classroom.objects.filter(IDdocente=user)
        rankings_por_aula = {}
        for aula in aulas:
            rankings_por_aula[aula] = Ranking.objects.filter(IDaula=aula).order_by('-puntos_totales')[:10]
    else:  # Estudiante
        # Rankings de las aulas donde está el estudiante
        aulas_estudiante = ClassroomStudent.objects.filter(IDestudiante=user)
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
        'game_types': GameType.objects.all(),
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
        'game_types': GameType.objects.all(),
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

# @login_required
# def notifications_list(request):
#     """Lista de notificaciones del usuario"""
#     # Por ahora retornamos una lista vacía
#     # Aquí implementarías la lógica para obtener notificaciones reales
#     notifications = []
#     
#     context = {
#         'notifications': notifications,
#     }
#     
#     return render(request, 'gamification/notifications_list.html', context)

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
def test_list(request):
    """Lista de tests para docentes"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden acceder a esta página.')
        return redirect('users:dashboard_teacher', user_id=request.user.id)
    
    tests = Test.objects.filter(IDdocente=request.user).order_by('-fecha_creacion')
    
    # Filtros
    classroom_id = request.GET.get('classroom')
    status = request.GET.get('status')
    search = request.GET.get('search')
    
    if classroom_id:
        tests = tests.filter(IDaula_id=classroom_id)
    if status:
        tests = tests.filter(activo=(status == 'active'))
    if search:
        tests = tests.filter(
            Q(titulo__icontains=search) |
            Q(descripcion__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(tests, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener aulas del docente
    classrooms = Classroom.objects.filter(teacher=request.user)
    
    context = {
        'page_obj': page_obj,
        'classrooms': classrooms,
        'filters': {
            'classroom_id': classroom_id,
            'status': status,
            'search': search,
        }
    }
    
    return render(request, 'gamification/test_list.html', context)

@login_required
def test_create(request):
    """Crear nuevo test"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden crear tests.')
        return redirect('users:dashboard_teacher', user_id=request.user.id)
    
    if request.method == 'POST':
        # Lógica para crear test
        titulo = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion')
        IDaula_id = request.POST.get('IDaula')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        tiempo_limite = request.POST.get('tiempo_limite', 30)
        puntos_por_pregunta = request.POST.get('puntos_por_pregunta', 10)
        activo = request.POST.get('activo') == 'on'
        
        if not all([titulo, IDaula_id, fecha_inicio, fecha_fin]):
            messages.error(request, 'Faltan datos requeridos.')
            return redirect('gamification:test_create')
        
        try:
            classroom = Classroom.objects.get(id=IDaula_id, teacher=request.user)
            
            test = Test.objects.create(
                titulo=titulo,
                descripcion=descripcion,
                IDaula=classroom,
                IDdocente=request.user,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                tiempo_limite=tiempo_limite,
                puntos_por_pregunta=puntos_por_pregunta,
                activo=activo
            )
            
            messages.success(request, 'Test creado exitosamente.')
            return redirect('gamification:test_edit', test_id=test.IDtest)
            
        except Exception as e:
            messages.error(request, f'Error al crear el test: {str(e)}')
    
    # Obtener aulas del docente
    classrooms = Classroom.objects.filter(teacher=request.user)
    
    context = {
        'classrooms': classrooms,
    }
    
    return render(request, 'gamification/test_create.html', context)

@login_required
def test_edit(request, test_id):
    """Editar test existente"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden editar tests.')
        return redirect('users:dashboard_teacher', user_id=request.user.id)
    
    test = get_object_or_404(Test, IDtest=test_id, IDdocente=request.user)
    
    if request.method == 'POST':
        # Lógica para actualizar test
        test.titulo = request.POST.get('titulo')
        test.descripcion = request.POST.get('descripcion')
        test.fecha_inicio = request.POST.get('fecha_inicio')
        test.fecha_fin = request.POST.get('fecha_fin')
        test.tiempo_limite = request.POST.get('tiempo_limite', 30)
        test.puntos_por_pregunta = request.POST.get('puntos_por_pregunta', 10)
        test.activo = request.POST.get('activo') == 'on'
        test.save()
        
        messages.success(request, 'Test actualizado exitosamente.')
        return redirect('gamification:test_detail', test_id=test.IDtest)
    
    # Obtener preguntas del test
    preguntas = Pregunta.objects.filter(IDtest=test).order_by('orden')
    
    context = {
        'test': test,
        'preguntas': preguntas,
    }
    
    return render(request, 'gamification/test_edit.html', context)

@login_required
def test_detail(request, test_id):
    """Detalle del test"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden ver detalles de tests.')
        return redirect('users:dashboard_teacher', user_id=request.user.id)
    
    test = get_object_or_404(Test, IDtest=test_id, IDdocente=request.user)
    
    # Obtener preguntas del test
    preguntas = Pregunta.objects.filter(IDtest=test).order_by('orden')
    
    # Obtener resultados del test
    resultados = ResultadoTest.objects.filter(IDtest=test).order_by('-fecha_fin')
    
    # Estadísticas
    total_estudiantes = ClassroomStudent.objects.filter(classroom=test.IDaula).count()
    estudiantes_completados = resultados.filter(completado=True).count()
    promedio_puntuacion = resultados.aggregate(Avg('porcentaje_acierto'))['porcentaje_acierto__avg'] or 0
    
    context = {
        'test': test,
        'preguntas': preguntas,
        'resultados': resultados,
        'total_estudiantes': total_estudiantes,
        'estudiantes_completados': estudiantes_completados,
        'promedio_puntuacion': promedio_puntuacion,
    }
    
    return render(request, 'gamification/test_detail.html', context)

@login_required
def test_results(request, test_id):
    """Resultados detallados del test"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden ver resultados de tests.')
        return redirect('users:dashboard_teacher', user_id=request.user.id)
    
    test = get_object_or_404(Test, IDtest=test_id, IDdocente=request.user)
    
    # Obtener todos los resultados
    resultados = ResultadoTest.objects.filter(IDtest=test).order_by('-porcentaje_acierto')
    
    # Estadísticas detalladas
    estadisticas = {
        'total_participantes': resultados.count(),
        'completados': resultados.filter(completado=True).count(),
        'promedio_puntuacion': resultados.aggregate(Avg('porcentaje_acierto'))['porcentaje_acierto__avg'] or 0,
        'mejor_puntuacion': resultados.aggregate(Max('porcentaje_acierto'))['porcentaje_acierto__max'] or 0,
        'peor_puntuacion': resultados.aggregate(Min('porcentaje_acierto'))['porcentaje_acierto__min'] or 0,
        'tiempo_promedio': resultados.aggregate(Avg('tiempo_empleado'))['tiempo_empleado__avg'] or 0,
    }
    
    context = {
        'test': test,
        'resultados': resultados,
        'estadisticas': estadisticas,
    }
    
    return render(request, 'gamification/test_results.html', context)

@login_required
def test_delete(request, test_id):
    """Eliminar test"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden eliminar tests.')
        return redirect('users:dashboard_teacher', user_id=request.user.id)
    
    test = get_object_or_404(Test, IDtest=test_id, IDdocente=request.user)
    
    if request.method == 'POST':
        test.delete()
        messages.success(request, 'Test eliminado exitosamente.')
        return redirect('gamification:test_list')
    
    return render(request, 'gamification/test_confirm_delete.html', {'test': test})

@login_required
def pregunta_create(request, test_id):
    """Crear nueva pregunta para un test"""
    if request.user.user_type != 2:  # Solo docentes
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    test = get_object_or_404(Test, IDtest=test_id, IDdocente=request.user)
    
    if request.method == 'POST':
        try:
            pregunta_texto = request.POST.get('pregunta')
            tipo_pregunta = request.POST.get('tipo_pregunta', 'opcion_multiple')
            puntos = request.POST.get('puntos', 10)
            orden = request.POST.get('orden', 1)
            
            if not pregunta_texto:
                return JsonResponse({'error': 'El texto de la pregunta es requerido'}, status=400)
            
            pregunta = Pregunta.objects.create(
                IDtest=test,
                pregunta=pregunta_texto,
                tipo_pregunta=tipo_pregunta,
                puntos=puntos,
                orden=orden
            )
            
            # Si es opción múltiple, crear opciones
            if tipo_pregunta == 'opcion_multiple':
                opciones_data = request.POST.getlist('opciones[]')
                correcta_index = int(request.POST.get('correcta_index', 0))
                
                for i, opcion_texto in enumerate(opciones_data):
                    if opcion_texto.strip():
                        Opcion.objects.create(
                            IDpregunta=pregunta,
                            texto=opcion_texto.strip(),
                            es_correcta=(i == correcta_index),
                            orden=i+1
                        )
            
            return JsonResponse({
                'success': True,
                'pregunta_id': pregunta.IDpregunta,
                'message': 'Pregunta creada exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def pregunta_edit(request, pregunta_id):
    """Editar pregunta existente"""
    if request.user.user_type != 2:  # Solo docentes
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    pregunta = get_object_or_404(Pregunta, IDpregunta=pregunta_id, IDtest__IDdocente=request.user)
    
    if request.method == 'POST':
        try:
            pregunta.pregunta = request.POST.get('pregunta')
            pregunta.tipo_pregunta = request.POST.get('tipo_pregunta', 'opcion_multiple')
            pregunta.puntos = request.POST.get('puntos', 10)
            pregunta.orden = request.POST.get('orden', 1)
            pregunta.save()
            
            # Actualizar opciones si es opción múltiple
            if pregunta.tipo_pregunta == 'opcion_multiple':
                # Eliminar opciones existentes
                pregunta.opcion_set.all().delete()
                
                # Crear nuevas opciones
                opciones_data = request.POST.getlist('opciones[]')
                correcta_index = int(request.POST.get('correcta_index', 0))
                
                for i, opcion_texto in enumerate(opciones_data):
                    if opcion_texto.strip():
                        Opcion.objects.create(
                            IDpregunta=pregunta,
                            texto=opcion_texto.strip(),
                            es_correcta=(i == correcta_index),
                            orden=i+1
                        )
            
            return JsonResponse({
                'success': True,
                'message': 'Pregunta actualizada exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def pregunta_delete(request, pregunta_id):
    """Eliminar pregunta"""
    if request.user.user_type != 2:  # Solo docentes
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    pregunta = get_object_or_404(Pregunta, IDpregunta=pregunta_id, IDtest__IDdocente=request.user)
    
    if request.method == 'POST':
        try:
            pregunta.delete()
            return JsonResponse({
                'success': True,
                'message': 'Pregunta eliminada exitosamente'
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def student_test_list(request):
    """Lista de tests disponibles para estudiantes"""
    if request.user.user_type != 1:  # Solo estudiantes
        messages.error(request, 'Solo los estudiantes pueden acceder a esta página.')
        return redirect('users:dashboard_student', user_id=request.user.id)
    
    # Obtener aulas del estudiante
    student_classrooms = ClassroomStudent.objects.filter(student=request.user).values_list('classroom', flat=True)
    
    # Obtener tests activos de las aulas del estudiante
    tests = Test.objects.filter(
        IDaula__in=student_classrooms,
        activo=True,
        fecha_inicio__lte=timezone.now(),
        fecha_fin__gte=timezone.now()
    ).order_by('-fecha_creacion')
    
    # Verificar si el estudiante ya completó cada test
    for test in tests:
        test.completado = ResultadoTest.objects.filter(
            IDtest=test,
            IDestudiante=request.user,
            completado=True
        ).exists()
    
    context = {
        'tests': tests,
    }
    
    return render(request, 'gamification/student_test_list.html', context)

@login_required
def take_test(request, test_id):
    """Tomar un test"""
    if request.user.user_type != 1:  # Solo estudiantes
        messages.error(request, 'Solo los estudiantes pueden tomar tests.')
        return redirect('users:dashboard_student', user_id=request.user.id)
    
    test = get_object_or_404(Test, IDtest=test_id, activo=True)
    
    # Verificar que el estudiante pertenece al aula
    if not ClassroomStudent.objects.filter(classroom=test.IDaula, student=request.user).exists():
        messages.error(request, 'No tienes acceso a este test.')
        return redirect('gamification:student_test_list')
    
    # Verificar que el test está en el período válido
    now = timezone.now()
    if now < test.fecha_inicio or now > test.fecha_fin:
        messages.error(request, 'Este test no está disponible en este momento.')
        return redirect('gamification:student_test_list')
    
    # Verificar si ya completó el test
    if ResultadoTest.objects.filter(IDtest=test, IDestudiante=request.user, completado=True).exists():
        messages.warning(request, 'Ya completaste este test.')
        return redirect('gamification:test_result', test_id=test_id)
    
    # Obtener preguntas del test
    preguntas = Pregunta.objects.filter(IDtest=test).order_by('orden')
    
    context = {
        'test': test,
        'preguntas': preguntas,
    }
    
    return render(request, 'gamification/take_test.html', context)

@login_required
def submit_test(request, test_id):
    """Enviar respuestas del test"""
    if request.user.user_type != 1:  # Solo estudiantes
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    test = get_object_or_404(Test, IDtest=test_id, activo=True)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Crear o actualizar resultado del test
        resultado, created = ResultadoTest.objects.get_or_create(
            IDtest=test,
            IDestudiante=request.user,
            defaults={
                'fecha_inicio': timezone.now(),
                'fecha_fin': timezone.now(),
                'completado': False
            }
        )
        
        if not created:
            resultado.fecha_fin = timezone.now()
        
        # Procesar respuestas
        preguntas = Pregunta.objects.filter(IDtest=test)
        puntuacion_total = 0
        preguntas_correctas = 0
        total_preguntas = preguntas.count()
        
        for pregunta in preguntas:
            respuesta_texto = request.POST.get(f'respuesta_{pregunta.IDpregunta}', '')
            opcion_id = request.POST.get(f'opcion_{pregunta.IDpregunta}')
            
            # Determinar si la respuesta es correcta
            es_correcta = False
            puntos_obtenidos = 0
            
            if pregunta.tipo_pregunta == 'opcion_multiple':
                if opcion_id:
                    opcion = Opcion.objects.get(IDopcion=opcion_id)
                    es_correcta = opcion.es_correcta
                    puntos_obtenidos = pregunta.puntos if es_correcta else 0
            elif pregunta.tipo_pregunta == 'verdadero_falso':
                respuesta_correcta = pregunta.opcion_set.filter(es_correcta=True).first()
                if respuesta_correcta:
                    es_correcta = respuesta_texto.lower() == respuesta_correcta.texto.lower()
                    puntos_obtenidos = pregunta.puntos if es_correcta else 0
            elif pregunta.tipo_pregunta == 'texto_corto':
                # Para texto corto, se requiere revisión manual
                puntos_obtenidos = 0
            
            # Guardar respuesta
            RespuestaEstudiante.objects.create(
                IDtest=test,
                IDpregunta=pregunta,
                IDestudiante=request.user,
                respuesta_texto=respuesta_texto,
                IDopcion_seleccionada_id=opcion_id if opcion_id else None,
                es_correcta=es_correcta,
                puntos_obtenidos=puntos_obtenidos
            )
            
            if es_correcta:
                preguntas_correctas += 1
                puntuacion_total += puntos_obtenidos
        
        # Actualizar resultado
        resultado.puntuacion_total = puntuacion_total
        resultado.puntuacion_maxima = total_preguntas * test.puntos_por_pregunta
        resultado.porcentaje_acierto = (preguntas_correctas / total_preguntas * 100) if total_preguntas > 0 else 0
        resultado.preguntas_correctas = preguntas_correctas
        resultado.total_preguntas = total_preguntas
        resultado.completado = True
        resultado.save()
        
        # Crear notificación
        Notification.objects.create(
            recipient=test.IDdocente,
            notification_type='quiz_completed',
            title=f'Test Completado: {test.titulo}',
            message=f'{request.user.get_full_name()} completó el test "{test.titulo}" con {resultado.porcentaje_acierto:.1f}% de acierto.'
        )
        
        return JsonResponse({
            'success': True,
            'resultado_id': resultado.IDresultado,
            'puntuacion': puntuacion_total,
            'porcentaje': float(resultado.porcentaje_acierto),
            'message': 'Test completado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def test_result(request, test_id):
    """Ver resultado del test"""
    if request.user.user_type != 1:  # Solo estudiantes
        messages.error(request, 'Solo los estudiantes pueden ver resultados de tests.')
        return redirect('users:dashboard_student', user_id=request.user.id)
    
    test = get_object_or_404(Test, IDtest=test_id)
    resultado = get_object_or_404(ResultadoTest, IDtest=test, IDestudiante=request.user)
    
    # Obtener respuestas detalladas
    respuestas = RespuestaEstudiante.objects.filter(
        IDtest=test,
        IDestudiante=request.user
    ).select_related('IDpregunta', 'IDopcion_seleccionada')
    
    context = {
        'test': test,
        'resultado': resultado,
        'respuestas': respuestas,
    }
    
    return render(request, 'gamification/test_result.html', context)

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
            aula = Classroom.objects.get(IDaula=aula_id, IDdocente=request.user)
        except Classroom.DoesNotExist:
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
        
        messages.success(request, f'Test duplicado exitosamente en "{aula.name}"')
        return redirect('gamification:test_detail', test_id=nuevo_test.IDtest)
    
    # Obtener aulas del docente
    aulas_docente = Classroom.objects.filter(IDdocente=request.user)
    
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

# ============================================================================
# MESSAGING SYSTEM VIEWS
# ============================================================================

@login_required
def messaging_dashboard(request):
    """Main messaging dashboard"""
    # Get user's conversations
    conversations = PrivateConversation.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).order_by('-updated_at')
    
    # Get user's classrooms for group chat
    if request.user.user_type == 2:  # Teacher
        classrooms = Classroom.objects.filter(IDdocente=request.user)
    else:  # Student
        classroom_relations = ClassroomStudent.objects.filter(IDestudiante=request.user)
        classrooms = Classroom.objects.filter(IDaula__in=classroom_relations.values_list('IDaula', flat=True))
    
    context = {
        'conversations': conversations,
        'classrooms': classrooms,
        'unread_count': get_unread_message_count(request.user)
    }
    return render(request, 'gamification/messaging_dashboard.html', context)

@login_required
def private_conversation_list(request):
    """List of private conversations"""
    conversations = PrivateConversation.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).order_by('-updated_at')
    
    context = {
        'conversations': conversations,
        'unread_count': get_unread_message_count(request.user)
    }
    return render(request, 'gamification/private_conversation_list.html', context)

@login_required
def private_conversation_detail(request, conversation_id):
    """Detail view of a private conversation"""
    conversation = get_object_or_404(PrivateConversation, id=conversation_id)
    
    # Check if user is part of this conversation
    if request.user not in [conversation.user1, conversation.user2]:
        return redirect('messaging_dashboard')
    
    other_user = conversation.get_other_user(request.user)
    messages = PrivateMessage.objects.filter(
        Q(sender=request.user, recipient=other_user) |
        Q(sender=other_user, recipient=request.user)
    ).order_by('created_at')
    
    # Mark messages as read
    messages.filter(recipient=request.user, is_read=False).update(is_read=True)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            message = PrivateMessage.objects.create(
                sender=request.user,
                recipient=other_user,
                subject=f"Message from {request.user.username}",
                content=content
            )
            # Create notification
            MessageNotification.objects.create(
                recipient=other_user,
                message=message
            )
            return redirect('private_conversation_detail', conversation_id=conversation_id)
    
    context = {
        'conversation': conversation,
        'other_user': other_user,
        'messages': messages,
        'unread_count': get_unread_message_count(request.user)
    }
    return render(request, 'gamification/private_conversation_detail.html', context)

@login_required
def new_private_message(request):
    """Create a new private message"""
    if request.method == 'POST':
        recipient_username = request.POST.get('recipient')
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        
        try:
            recipient = User.objects.get(username=recipient_username)
            message = PrivateMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                subject=subject,
                content=content
            )
            # Create notification
            MessageNotification.objects.create(
                recipient=recipient,
                message=message
            )
            return redirect('messaging_dashboard')
        except User.DoesNotExist:
            context = {
                'error': 'User not found',
                'unread_count': get_unread_message_count(request.user)
            }
            return render(request, 'gamification/new_private_message.html', context)
    
    context = {
        'unread_count': get_unread_message_count(request.user)
    }
    return render(request, 'gamification/new_private_message.html', context)

@login_required
def search_users(request):
    """Search users for messaging"""
    query = request.GET.get('q', '')
    users = []
    
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
        ).exclude(id=request.user.id)[:10]
    
    context = {
        'users': users,
        'query': query,
        'unread_count': get_unread_message_count(request.user)
    }
    return render(request, 'gamification/search_users.html', context)

@login_required
def classroom_chat(request, classroom_id):
    """Group chat for a classroom"""
    classroom = get_object_or_404(Classroom, id=classroom_id)
    
    # Check permissions
    if request.user.user_type == 2:  # Teacher
        if classroom.IDdocente != request.user:
            return redirect('messaging_dashboard')
    else:  # Student
        if not ClassroomStudent.objects.filter(IDaula=classroom, IDestudiante=request.user).exists():
            return redirect('messaging_dashboard')
    
    messages = ClassroomMessage.objects.filter(classroom=classroom).order_by('created_at')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            ClassroomMessage.objects.create(
                classroom=classroom,
                sender=request.user,
                content=content
            )
            return redirect('classroom_chat', classroom_id=classroom_id)
    
    context = {
        'classroom': classroom,
        'messages': messages,
        'unread_count': get_unread_message_count(request.user)
    }
    return render(request, 'gamification/classroom_chat.html', context)

@login_required
def message_notifications(request):
    """List of message notifications"""
    notifications = MessageNotification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')
    
    # Mark as read
    notifications.update(is_read=True)
    
    context = {
        'notifications': notifications,
        'unread_count': get_unread_message_count(request.user)
    }
    return render(request, 'gamification/message_notifications.html', context)

def get_unread_message_count(user):
    """Get count of unread messages for a user"""
    return PrivateMessage.objects.filter(recipient=user, is_read=False).count()

# API Views for real-time updates
@login_required
def get_unread_count_api(request):
    """API to get unread message count"""
    count = get_unread_message_count(request.user)
    return JsonResponse({'count': count})

@login_required
def get_new_messages_api(request, conversation_id):
    """API to get new messages for a conversation"""
    conversation = get_object_or_404(PrivateConversation, id=conversation_id)
    other_user = conversation.get_other_user(request.user)
    
    last_message_id = request.GET.get('last_message_id', 0)
    new_messages = PrivateMessage.objects.filter(
        Q(sender=request.user, recipient=other_user) |
        Q(sender=other_user, recipient=request.user),
        id__gt=last_message_id
    ).order_by('created_at')
    
    messages_data = []
    for message in new_messages:
        messages_data.append({
            'id': message.id,
            'sender': message.sender.username,
            'content': message.content,
            'created_at': message.created_at.strftime('%H:%M'),
            'is_own': message.sender == request.user
        })
    
    return JsonResponse({'messages': messages_data})

@login_required
def gamification_dashboard(request):
    """Dashboard principal de gamificación"""
    user = request.user
    
    # Crear nivel si no existe
    nivel_obj = crear_nivel_usuario(user)
    
    # Obtener estadísticas
    stats = obtener_estadisticas_usuario(user)
    
    # Obtener insignias del usuario
    insignias_usuario = InsigniasUsuario.objects.filter(IDusuario=user).select_related('IDinsignia')
    
    # Obtener actividades recientes
    actividades_recientes = LogGamificacion.objects.filter(
        IDusuario=user
    ).order_by('-fecha_evento')[:10]
    
    context = {
        'user': user,
        'nivel': nivel_obj,
        'stats': stats,
        'insignias_usuario': insignias_usuario,
        'actividades_recientes': actividades_recientes,
    }
    
    return render(request, 'gamification/dashboard.html', context)

@login_required
def test_activity_completion(request):
    """Vista de prueba para completar una actividad"""
    if request.method == 'POST':
        actividad_tipo = request.POST.get('actividad_tipo', 'Quiz')
        puntuacion = int(request.POST.get('puntuacion', 100))
        
        # Asignar puntuación
        resultado = asignar_puntuacion_actividad(
            user=request.user,
            actividad_tipo=actividad_tipo,
            puntuacion_porcentaje=puntuacion
        )
        
        if resultado:
            return JsonResponse({
                'success': True,
                'puntos_ganados': resultado['puntos_ganados'],
                'puntos_acumulados': resultado['puntos_acumulados'],
                'nivel_actual': resultado['nivel_actual'],
                'subio_nivel': resultado['subio_nivel'],
                'insignias_desbloqueadas': resultado['insignias_desbloqueadas']
            })
        else:
            return JsonResponse({'success': False, 'error': 'Error al asignar puntuación'})
    
    return render(request, 'gamification/test_activity.html')

@login_required
def user_stats(request):
    """Vista para mostrar estadísticas detalladas del usuario"""
    user = request.user
    stats = obtener_estadisticas_usuario(user)
    
    if not stats:
        # Crear nivel si no existe
        crear_nivel_usuario(user)
        stats = obtener_estadisticas_usuario(user)
    
    context = {
        'user': user,
        'stats': stats,
    }
    
    return render(request, 'gamification/user_stats.html', context)

@login_required
def achievements_list(request):
    """Vista para mostrar logros del usuario"""
    user = request.user
    
    # Obtener insignias del usuario
    insignias_usuario = InsigniasUsuario.objects.filter(IDusuario=user).select_related('IDinsignia')
    
    # Obtener todas las insignias disponibles
    todas_insignias = Insignias.objects.all()
    
    # Marcar cuáles tiene el usuario
    for insignia in todas_insignias:
        insignia.obtenida = insignias_usuario.filter(IDinsignia=insignia).exists()
    
    context = {
        'user': user,
        'insignias_usuario': insignias_usuario,
        'todas_insignias': todas_insignias,
    }
    
    return render(request, 'gamification/achievements.html', context)

@login_required
def assignment_create(request):
    """Vista para crear tareas/actividades"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden crear actividades.')
        return redirect('gamification:dashboard')
    
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion')
        aula_id = request.POST.get('aula_id')
        tipo_actividad_id = request.POST.get('tipo_actividad')
        try:
            aula = Classroom.objects.get(id=aula_id, teacher=request.user)
            tipo_actividad = ActivityType.objects.get(IDtipoActividad=tipo_actividad_id)
            actividad = Activities.objects.create(
                Titulo=titulo,
                Instrucciones=descripcion,
                IDtipoActividad=tipo_actividad,
                IDficha=1,  # Por defecto
                IDaula=aula
            )
            messages.success(request, f'Actividad "{titulo}" creada exitosamente.')
            return redirect('gamification:aula_detail', aula_id=aula.id)
        except Classroom.DoesNotExist:
            messages.error(request, 'Aula no encontrada o no tienes permisos.')
        except ActivityType.DoesNotExist:
            messages.error(request, 'Tipo de actividad no válido.')
        except Exception as e:
            messages.error(request, f'Error al crear la actividad: {str(e)}')
        return redirect('gamification:dashboard')
    # Si es GET, devolver 404
    from django.http import Http404
    raise Http404('La creación de tareas solo está disponible mediante el modal.')

