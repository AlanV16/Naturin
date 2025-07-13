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
    Activities, ActivityType, GameType, Games, UserGame, Progress, Levels, Badges, UserBadge, 
    Challenges, UserChallenge, UserReward, UserStatistics, GamificationLog, Question, Option, 
    Classroom, ClassroomStudent, Notification, Test
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
    nivel, created = Levels.objects.get_or_create(user=user)
    
    # Obtener o crear estadísticas del usuario
    estadisticas, created = UserStatistics.objects.get_or_create(user=user)
    
    # Obtener insignias del usuario
    insignias_usuario = UserBadge.objects.filter(user=user)
    
    # Juegos más populares
    popular_games = Games.objects.annotate(
        play_count=Count('usergame')
    ).order_by('-play_count')[:5]
    
    # Juegos recientes del usuario
    recent_sessions = UserGame.objects.filter(user=user).order_by('-FechaJugada')[:5]
    
    # Aulas del usuario (si es estudiante)
    aulas_usuario = []
    if hasattr(user, 'aulas'):
        aulas_usuario = user.aulas.all()
    
    # Actividades asignadas al usuario
    actividades_asignadas = []
    for aula_estudiante in ClassroomStudent.objects.filter(student=user):
        actividades_asignadas.extend(aula_estudiante.classroom.actividades_set.all())
    
    # Desafíos disponibles
    desafios_disponibles = Challenges.objects.filter(
        active=True,
        level_minimo__lte=nivel.level,
        fecha_inicio__lte=timezone.now(),
        fecha_fin__gte=timezone.now()
    )
    
    context = {
        'total_games_played': estadisticas.juegos_jugados,
        'total_points': nivel.puntos_acumulados,
        'user_level': nivel.level,
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
    games = Games.objects.all()
    
    # Filtros
    game_type = request.GET.get('type')
    difficulty = request.GET.get('difficulty')
    
    if game_type:
        games = games.filter(game_type_id=game_type)
    if difficulty:
        games = games.filter(difficulty=difficulty)
    
    # Ordenamiento
    sort_by = request.GET.get('sort', 'IDjuego')
    if sort_by == 'popular':
        games = games.annotate(play_count=Count('usergame')).order_by('-play_count')
    elif sort_by == 'recent':
        games = games.order_by('-IDjuego')
    elif sort_by == 'difficulty':
        games = games.order_by('difficulty')
    
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
        return redirect('gamification/dashboard')
    
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
    actividades = Activities.objects.filter(classroom=aula).order_by('-id')
    
    # Rankings del aula
    rankings = Ranking.objects.filter(classroom=aula).order_by('-total_points')[:10]
    
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
    
    aula = get_object_or_404(Classroom, id=aula_id, teacher=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        instructions = request.POST.get('instructions')
        activity_type_id = request.POST.get('activity_type')
        ficha_id = request.POST.get('ficha_id', 1)  # Por defecto
        
        activity = Activities.objects.create(
            title=title,
            instructions=instructions,
            activity_type_id=activity_type_id,
            ficha_id=ficha_id,
            classroom=aula
        )
        
        messages.success(request, f'Actividad "{title}" creada exitosamente.')
        return redirect('gamification:aula_detail', aula_id=aula.id)
    
    context = {
        'aula': aula,
        'activity_types': ActivityType.objects.all(),
    }
    
    return render(request, 'gamification/actividad_create.html', context)

@login_required
def actividad_detail(request, activity_id):
    """Detalle de una actividad con progreso de estudiantes"""
    activity = get_object_or_404(Activities, id=activity_id)
    
    # Verificar que el usuario tenga acceso a esta actividad
    if request.user.user_type == 1:  # Estudiante
        if not ClassroomStudent.objects.filter(student=request.user, classroom=activity.classroom).exists():
            messages.error(request, 'No tienes acceso a esta actividad.')
            return redirect('gamification:dashboard')
    elif request.user.user_type == 2:  # Docente
        if activity.classroom.teacher != request.user:
            messages.error(request, 'No tienes acceso a esta actividad.')
            return redirect('gamification:dashboard')
    
    # Progreso de estudiantes en esta actividad
    progress = Progress.objects.filter(activity=activity).order_by('-Fecha')
    
    context = {
        'activity': activity,
        'progress': progress,
    }
    
    return render(request, 'gamification/actividad_detail.html', context)

# ============================================================================
# VISTAS DE DESAFÍOS
# ============================================================================

@login_required
def desafios_list(request):
    """Lista de desafíos disponibles para el usuario"""
    user = request.user
    nivel, created = Levels.objects.get_or_create(user=user)
    
    # Desafíos disponibles según el nivel del usuario
    desafios_disponibles = Challenges.objects.filter(
        active=True,
        level_minimo__lte=nivel.level,
        fecha_inicio__lte=timezone.now(),
        fecha_fin__gte=timezone.now()
    )
    
    # Progreso del usuario en desafíos
    progreso_desafios = UserChallenge.objects.filter(user=user)
    
    context = {
        'desafios_disponibles': desafios_disponibles,
        'progreso_desafios': progreso_desafios,
        'user_level': nivel.level,
    }
    
    return render(request, 'gamification/desafios_list.html', context)

@login_required
def desafio_detail(request, challenge_id):
    """Detalle de un desafío específico"""
    challenge = get_object_or_404(Challenges, id=challenge_id, active=True)
    user = request.user
    
    # Verificar si el usuario puede acceder al desafío
    nivel, created = Levels.objects.get_or_create(user=user)
    if nivel.level < challenge.level_minimo:
        messages.error(request, f'Necesitas nivel {challenge.level_minimo} para acceder a este desafío.')
        return redirect('gamification:desafios_list')
    
    # Progreso del usuario en este desafío
    progreso, created = UserChallenge.objects.get_or_create(
        user=user,
        challenge=challenge
    )
    
    context = {
        'challenge': challenge,
        'progreso': progreso,
        'user_level': nivel.level,
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
        aulas = Classroom.objects.filter(teacher=user)
        rankings_por_aula = {}
        for aula in aulas:
            rankings_por_aula[aula] = Ranking.objects.filter(classroom=aula).order_by('-total_points')[:10]
    else:  # Estudiante
        # Rankings de las aulas donde está el estudiante
        aulas_estudiante = ClassroomStudent.objects.filter(student=user)
        rankings_por_aula = {}
        for aula_est in aulas_estudiante:
            rankings_por_aula[aula_est.classroom] = Ranking.objects.filter(classroom=aula_est.classroom).order_by('-total_points')[:10]
    
    context = {
        'rankings_por_aula': rankings_por_aula,
    }
    
    return render(request, 'gamification/rankings_list.html', context)

@login_required
def estadisticas_personales(request):
    """Estadísticas personales del usuario"""
    user = request.user
    
    # Obtener nivel y estadísticas
    nivel, created = Levels.objects.get_or_create(user=user)
    estadisticas, created = UserStatistics.objects.get_or_create(user=user)
    
    # Obtener insignias
    insignias = UserBadge.objects.filter(user=user)
    
    # Historial de actividades
    historial_actividades = Progress.objects.filter(user=user).order_by('-Fecha')[:20]
    
    # Historial de juegos
    historial_juegos = UserGame.objects.filter(user=user).order_by('-FechaJugada')[:20]
    
    # Logs de gamificación
    logs = GamificationLog.objects.filter(user=user).order_by('-event_date')[:50]
    
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
        game_type_id = request.POST.get('game_type')
        difficulty = request.POST.get('difficulty')
        instructions = request.POST.get('instructions')
        
        game = Games.objects.create(
            name=nombre,
            description=descripcion,
            game_type_id=game_type_id,
            difficulty=difficulty,
            instructions=instructions
        )
        
        messages.success(request, f'Juego "{nombre}" creado exitosamente.')
        return redirect('gamification:game_edit', game_id=game.id)
    
    context = {
        'game_types': GameType.objects.all(),
        'difficulties': [(1, 'Fácil'), (2, 'Básico'), (3, 'Intermedio'), (4, 'Avanzado'), (5, 'Experto')],
    }
    
    return render(request, 'gamification/game_create.html', context)

@login_required
def game_edit(request, game_id):
    """Editar un juego existente"""
    game = get_object_or_404(Games, id=game_id)
    
    if request.method == 'POST':
        game.name = request.POST.get('nombre')
        game.description = request.POST.get('descripcion')
        game.difficulty = int(request.POST.get('difficulty', 1))
        game.instructions = request.POST.get('instructions')
        
        game.save()
        messages.success(request, 'Juego actualizado exitosamente.')
        return redirect('gamification:game_edit', game_id=game.id)
    
    context = {
        'game': game,
        'difficulties': [(1, 'Fácil'), (2, 'Básico'), (3, 'Intermedio'), (4, 'Avanzado'), (5, 'Experto')],
        'game_types': GameType.objects.all(),
    }
    
    return render(request, 'gamification/game_edit.html', context)

@login_required
def quiz_play(request, game_id):
    """Jugar un cuestionario"""
    game = get_object_or_404(Games, id=game_id)
    
    # Registrar juego del usuario
    user_game = UserGame.objects.create(
        user=request.user,
        game=game,
        score=0
    )
        
    # Obtener nivel del usuario
    nivel, created = Levels.objects.get_or_create(user=request.user)
    
    context = {
        'game': game,
        'user_level': nivel.level,
        'session_id': user_game.id,
    }
    
    return render(request, 'gamification/quiz_play.html', context)

@login_required
def rapid_questions_play(request, game_id):
    """Jugar preguntas rápidas"""
    game = get_object_or_404(Games, id=game_id)
    
    # Registrar juego del usuario
    user_game = UserGame.objects.create(
        user=request.user,
        game=game,
        score=0
    )
    
    context = {
        'game': game,
        'session_id': user_game.id,
    }
    
    return render(request, 'gamification/rapid_questions_play.html', context)

@login_required
def leaderboard(request, game_id=None):
    """Tabla de clasificación"""
    if game_id:
        # Ranking específico de un juego
        rankings = Ranking.objects.filter(game_id=game_id).order_by('-total_points')
        game = get_object_or_404(Games, id=game_id)
    else:
        # Ranking general
        rankings = Ranking.objects.all().order_by('-total_points')
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
    nivel, created = Levels.objects.get_or_create(user=user)
    estadisticas, created = UserStatistics.objects.get_or_create(user=user)
    
    # Obtener insignias
    insignias = UserBadge.objects.filter(user=user)
    
    # Obtener historial de juegos
    historial_juegos = UserGame.objects.filter(user=user).order_by('-FechaJugada')[:10]
    
    # Obtener progreso en actividades
    progreso_actividades = Progress.objects.filter(user=user).order_by('-Fecha')[:10]
    
    # Obtener desafíos completados
    desafios_completados = UserChallenge.objects.filter(
        user=user, 
        completed=True
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
        game = get_object_or_404(Games, id=game_id)
        
        # Aquí deberías implementar la lógica para obtener preguntas
        # Por ahora retornamos datos de ejemplo
        questions_data = {
            'game_id': game_id,
            'game_name': game.name,
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
            nivel, created = Levels.objects.get_or_create(user=user)
            nivel.puntos_acumulados += 10  # Puntos por respuesta
            nivel.actualizar_nivel()
            nivel.save()
            # Registrar log
            GamificationLog.objects.create(
                user=user,
                tipo_evento='respuesta_correcta',
                description=f'Respuesta correcta en pregunta {question_id}',
                points_earned=10
            )
            return JsonResponse({
                'success': True,
                'points_earned': 10,
                'new_total_points': nivel.puntos_acumulados,
                'new_level': nivel.level
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
    aula = get_object_or_404(Classroom, id=aula_id)
    
    # Verificar permisos
    if request.user.user_type == 2:  # Docente
        if aula.teacher != request.user:
            messages.error(request, 'No tienes permisos para ver esta aula.')
            return redirect('gamification:dashboard')
        tests = Test.objects.filter(classroom=aula).order_by('-created_at')
    else:  # Estudiante
        if not ClassroomStudent.objects.filter(student=request.user, classroom=aula).exists():
            messages.error(request, 'No tienes acceso a esta aula.')
            return redirect('gamification:dashboard')
        tests = Test.objects.filter(classroom=aula, active=True).order_by('-created_at')
    
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
        is_public=True,
        teacher__user_type=2  # Solo de docentes
    ).exclude(teacher=request.user).order_by('-created_at')
    
    # Obtener aulas del docente
    aulas_docente = Classroom.objects.filter(teacher=request.user)
    
    # Calcular número de docentes activos
    docentes_activos = tests_publicos.values('teacher').distinct().count()
    
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
    
    test_original = get_object_or_404(Test, id=test_id, is_public=True)
    aula_destino_id = request.POST.get('aula_destino')
    
    if not aula_destino_id:
        messages.error(request, 'Debes seleccionar una aula de destino.')
        return redirect('gamification:test_public_list')
    
    aula_destino = get_object_or_404(Classroom, id=aula_destino_id, teacher=request.user)
    
    try:
        nuevo_test = test_original.copy_test(request.user, aula_destino)
        messages.success(request, f'Test "{test_original.title}" copiado exitosamente a {aula_destino.name}.')
        return redirect('gamification:test_edit', test_id=nuevo_test.id)
    except Exception as e:
        messages.error(request, f'Error al copiar el test: {str(e)}')
        return redirect('gamification:test_public_list')

@login_required
def test_make_public(request, test_id):
    """Hacer público un test para que otros docentes puedan copiarlo"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden hacer públicos los tests.')
        return redirect('gamification:dashboard')
    
    test = get_object_or_404(Test, id=test_id, teacher=request.user)
    
    if request.method == 'POST':
        test.is_public = True
        test.save()
        messages.success(request, f'Test "{test.title}" ahora es público y otros docentes pueden copiarlo.')
        return redirect('gamification:test_detail', test_id=test.id)
    
    return redirect('gamification:test_detail', test_id=test.id)

@login_required
def test_create(request, aula_id):
    """Crear un nuevo test para un aula con preguntas incluidas"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden crear tests.')
        return redirect('gamification:dashboard')
    
    aula = get_object_or_404(Classroom, id=aula_id, teacher=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        time_limit = request.POST.get('time_limit', 30)
        points_per_question = request.POST.get('points_per_question', 10)
        is_public = request.POST.get('is_public') == 'on'
        
        try:
            from django.utils.dateparse import parse_datetime
            start_date = parse_datetime(start_date)
            end_date = parse_datetime(end_date)
            
            questions_data = request.POST.getlist('questions[]')
            question_types = request.POST.getlist('question_types[]')
            points_questions = request.POST.getlist('points_questions[]')
            valid_questions = [q for q in questions_data if q.strip()]
            if not valid_questions:
                messages.error(request, 'Debes agregar al menos una pregunta válida al test.')
                return render(request, 'gamification/test_create.html', {'aula': aula})
            
            test = Test.objects.create(
                title=title,
                description=description,
                classroom=aula,
                teacher=request.user,
                start_date=start_date,
                end_date=end_date,
                time_limit=int(time_limit),
                points_per_question=int(points_per_question),
                is_public=is_public
            )
            
            # Procesar preguntas del formulario
            for i, (question_text, question_type, points) in enumerate(zip(questions_data, question_types, points_questions)):
                if question_text.strip():  # Solo crear preguntas no vacías
                    question = Question.objects.create(
                        test=test,
                        question=question_text,
                        question_type=question_type,
                        points=int(points),
                        order=i+1
                    )
                    # Si es opción múltiple, crear las opciones
                    if question_type == 'opcion_multiple':
                        options = request.POST.getlist(f'options_{i}[]')
                        correct_option = request.POST.get(f'correct_option_{i}')
                        for j, option_text in enumerate(options):
                            if option_text.strip():
                                Option.objects.create(
                                    question=question,
                                    text=option_text,
                                    is_correct=str(j) == correct_option,
                                    order=j+1
                                )
            messages.success(request, f'Test "{title}" creado exitosamente con {test.question_set.count()} preguntas.')
            return redirect('gamification:test_list', aula_id=aula.id)
        except Exception as e:
            messages.error(request, f'Error al crear el test: {str(e)}')
    context = {
        'aula': aula,
    }
    return render(request, 'gamification/test_create.html', context)

@login_required
def test_detail(request, test_id):
    """Detalle de un test con sus preguntas"""
    test = get_object_or_404(Test, id=test_id)
    
    # Verificar permisos
    if request.user.user_type == 2:  # Docente
        if test.teacher != request.user:
            messages.error(request, 'No tienes permisos para ver este test.')
            return redirect('gamification:dashboard')
    else:  # Estudiante
        if not ClassroomStudent.objects.filter(student=request.user, classroom=test.classroom).exists():
            messages.error(request, 'No tienes acceso a este test.')
            return redirect('gamification:dashboard')
    
    questions = Question.objects.filter(test=test).order_by('order')
    
    # Si es estudiante, verificar si ya completó el test
    resultado_estudiante = None
    if request.user.user_type == 1:  # Estudiante
        resultado_estudiante = ResultadoTest.objects.filter(
            test=test,
            student=request.user
        ).first()
    
    context = {
        'test': test,
        'questions': questions,
        'resultado_estudiante': resultado_estudiante,
    }
    
    return render(request, 'gamification/test_detail.html', context)

@login_required
def test_edit(request, test_id):
    """Editar un test existente"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden editar tests.')
        return redirect('gamification:dashboard')
    
    test = get_object_or_404(Test, id=test_id, teacher=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        time_limit = request.POST.get('time_limit')
        points_per_question = request.POST.get('points_per_question')
        active = request.POST.get('active') == 'on'
        
        try:
            from django.utils.dateparse import parse_datetime
            start_date = parse_datetime(start_date)
            end_date = parse_datetime(end_date)
            
            test.title = title
            test.description = description
            test.start_date = start_date
            test.end_date = end_date
            test.time_limit = int(time_limit)
            test.points_per_question = int(points_per_question)
            test.active = active
            test.save()
            
            messages.success(request, f'Test "{title}" actualizado exitosamente.')
            return redirect('gamification:test_detail', test_id=test.id)
            
        except Exception as e:
            messages.error(request, f'Error al actualizar el test: {str(e)}')
    
    context = {
        'test': test,
        'max_score': test.question_set.count() * test.points_per_question,
    }
    
    return render(request, 'gamification/test_edit.html', context)

@login_required
def pregunta_create(request, test_id):
    """Crear una nueva pregunta para un test"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden crear preguntas.')
        return redirect('gamification:dashboard')
    
    test = get_object_or_404(Test, id=test_id, teacher=request.user)
    
    if request.method == 'POST':
        question_text = request.POST.get('question')
        question_type = request.POST.get('question_type')
        points = request.POST.get('points', 10)
        order = request.POST.get('order', 1)
        
        try:
            question = Question.objects.create(
                test=test,
                question=question_text,
                question_type=question_type,
                points=int(points),
                order=int(order)
            )
            
            # Si es opción múltiple, crear las opciones
            if question_type == 'opcion_multiple':
                options = request.POST.getlist('options[]')
                correct_option = request.POST.get('correct_option')
                
                for i, option_text in enumerate(options):
                    if option_text.strip():  # Solo crear opciones no vacías
                        Option.objects.create(
                            question=question,
                            text=option_text,
                            is_correct=str(i) == correct_option,
                            order=i+1
                        )
            
            messages.success(request, 'Pregunta creada exitosamente.')
            return redirect('gamification:test_detail', test_id=test.id)
            
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
    
    test = get_object_or_404(Test, id=test_id, active=True)
    
    # Verificar que el estudiante está inscrito en el aula
    if not ClassroomStudent.objects.filter(student=request.user, classroom=test.classroom).exists():
        messages.error(request, 'No tienes acceso a este test.')
        return redirect('gamification:dashboard')
    
    # Verificar fechas del test
    now = timezone.now()
    if now < test.start_date or now > test.end_date:
        messages.error(request, 'Este test no está disponible en este momento.')
        return redirect('gamification:test_detail', test_id=test.id)
    
    # Verificar si ya completó el test
    resultado_existente = ResultadoTest.objects.filter(
        test=test,
        student=request.user,
        completed=True
    ).first()
    
    if resultado_existente:
        messages.warning(request, 'Ya completaste este test.')
        return redirect('gamification:test_detail', test_id=test.id)
    
    # Obtener preguntas del test
    questions = Question.objects.filter(test=test).order_by('order')
    
    if request.method == 'POST':
        # Procesar respuestas del estudiante
        total_score = 0
        correct_questions = 0
        total_questions = questions.count()
        
        for question in questions:
            if question.question_type == 'opcion_multiple':
                option_id = request.POST.get(f'question_{question.id}')
                if option_id:
                    option = Option.objects.get(id=option_id)
                    is_correct = option.is_correct
                    points_earned = question.points if is_correct else 0
                    
                    RespuestaEstudiante.objects.create(
                        test=test,
                        question=question,
                        student=request.user,
                        option_selected=option,
                        is_correct=is_correct,
                        points_earned=points_earned
                    )
                    
                    if is_correct:
                        correct_questions += 1
                        total_score += points_earned
            
            elif question.question_type == 'verdadero_falso':
                answer = request.POST.get(f'question_{question.id}')
                if answer:
                    # Aquí implementarías la lógica para verdadero/falso
                    pass
            
            elif question.question_type == 'texto_corto':
                answer_text = request.POST.get(f'question_{question.id}')
                if answer_text:
                    RespuestaEstudiante.objects.create(
                        test=test,
                        question=question,
                        student=request.user,
                        answer_text=answer_text,
                        points_earned=0  # Requiere revisión manual
                    )
        
        # Crear resultado del test
        percentage_correct = (correct_questions / total_questions * 100) if total_questions > 0 else 0
        
        ResultadoTest.objects.create(
            test=test,
            student=request.user,
            total_score=total_score,
            max_score=total_questions * test.points_per_question,
            percentage_correct=percentage_correct,
            correct_questions=correct_questions,
            total_questions=total_questions,
            start_date=now,
            end_date=now,
            completed=True
        )
        
        # Actualizar nivel del estudiante
        nivel, created = Levels.objects.get_or_create(user=request.user)
        nivel.puntos_acumulados += total_score
        nivel.actualizar_nivel()
        nivel.save()
        
        messages.success(request, f'Test completado. Puntuación: {total_score} puntos.')
        return redirect('gamification:test_results', test_id=test.id)
    
    context = {
        'test': test,
        'questions': questions,
    }
    
    return render(request, 'gamification/test_take.html', context)

@login_required
def test_results(request, test_id):
    """Ver resultados de un test"""
    test = get_object_or_404(Test, id=test_id)
    
    # Verificar permisos
    if request.user.user_type == 1:  # Estudiante
        if not test.active:
            messages.error(request, 'Este test no está disponible.')
            return redirect('gamification:dashboard')
        # Solo mostrar su propio resultado
        resultados = ResultadoTest.objects.filter(test=test, student=request.user)
    else:  # Docente
        if test.teacher != request.user:
            messages.error(request, 'No tienes permisos para ver estos resultados.')
            return redirect('gamification:dashboard')
        # Mostrar todos los resultados
        resultados = ResultadoTest.objects.filter(test=test).order_by('-end_date')
    
    context = {
        'test': test,
        'resultados': resultados,
    }
    
    return render(request, 'gamification/test_results.html', context)

@login_required
def test_delete(request, test_id):
    """Eliminar un test"""
    test = get_object_or_404(Test, id=test_id, teacher=request.user)
    
    if request.method == 'POST':
        title = test.title
        test.delete()
        messages.success(request, f'Test "{title}" eliminado exitosamente.')
        return redirect('users:dashboard_teacher')
    
    context = {
        'test': test,
    }
    
    return render(request, 'gamification/test_confirm_delete.html', context)

@login_required
def test_results_detail(request, resultado_id):
    """Ver detalle de un resultado específico"""
    resultado = get_object_or_404(ResultadoTest, id=resultado_id)
    
    # Verificar permisos
    if request.user.user_type == 1:  # Estudiante
        if resultado.student != request.user:
            messages.error(request, 'No tienes permisos para ver este resultado.')
            return redirect('gamification:dashboard')
    else:  # Docente
        if resultado.test.teacher != request.user:
            messages.error(request, 'No tienes permisos para ver este resultado.')
            return redirect('gamification:dashboard')
    
    # Obtener respuestas detalladas
    respuestas = RespuestaEstudiante.objects.filter(resultado=resultado)
    
    context = {
        'resultado': resultado,
        'respuestas': respuestas,
    }
    
    return render(request, 'gamification/test_results_detail.html', context)

@login_required
def test_export_results(request, test_id):
    """Exportar resultados de un test"""
    test = get_object_or_404(Test, id=test_id, teacher=request.user)
    
    if request.method == 'POST':
        formato = request.POST.get('formato', 'csv')
        
        resultados = ResultadoTest.objects.filter(test=test).order_by('-end_date')
        
        if formato == 'csv':
            import csv
            from django.http import HttpResponse
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="resultados_{test.title}.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Estudiante', 'Puntuación', 'Porcentaje', 'Preguntas Correctas', 'Tiempo Empleado', 'Fecha'])
            
            for resultado in resultados:
                writer.writerow([
                    resultado.student.username,
                    resultado.total_score,
                    f"{resultado.percentage_correct:.1f}%",
                    resultado.correct_questions,
                    f"{resultado.time_taken}s",
                    resultado.end_date.strftime("%d/%m/%Y %H:%M")
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
    test = get_object_or_404(Test, id=test_id)
    
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden duplicar tests.')
        return redirect('gamification:dashboard')
    
    if request.method == 'POST':
        aula_id = request.POST.get('aula_destino')
        if not aula_id:
            messages.error(request, 'Debes seleccionar un aula de destino.')
            return redirect('gamification:test_detail', test_id=test_id)
        
        try:
            aula = Classroom.objects.get(id=aula_id, teacher=request.user)
        except Classroom.DoesNotExist:
            messages.error(request, 'Aula no válida.')
            return redirect('gamification:test_detail', test_id=test_id)
        
        # Crear copia del test
        nuevo_test = Test.objects.create(
            title=f"{test.title} (Copia)",
            description=test.description,
            time_limit=test.time_limit,
            points_per_question=test.points_per_question,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
            classroom=aula,
            teacher=request.user,
            active=False,  # Inactivo por defecto
            is_public=False,
            is_copy=True
        )
        
        # Copiar preguntas
        for question in test.question_set.all():
            nueva_pregunta = Question.objects.create(
                question=question.question,
                question_type=question.question_type,
                points=question.points,
                order=question.order,
                test=nuevo_test
            )
            
            # Copiar opciones si es de opción múltiple
            if question.question_type == 'opcion_multiple':
                for option in question.option_set.all():
                    Option.objects.create(
                        text=option.text,
                        is_correct=option.is_correct,
                        question=nueva_pregunta
                    )
        
        messages.success(request, f'Test duplicado exitosamente en "{aula.name}"')
        return redirect('gamification:test_detail', test_id=nuevo_test.id)
    
    # Obtener aulas del docente
    aulas_docente = Classroom.objects.filter(teacher=request.user)
    
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
    game_stats, created = UserStatistics.objects.get_or_create(user=user)
    
    # Obtener progreso del usuario
    progreso, created = Progress.objects.get_or_create(user=user)
    
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
    game_stats, created = UserStatistics.objects.get_or_create(user=user)
    
    # Obtener progreso del usuario
    progreso, created = Progress.objects.get_or_create(user=user)
    
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
    game_stats, created = UserStatistics.objects.get_or_create(user=user)
    
    # Obtener progreso del usuario
    progreso, created = Progress.objects.get_or_create(user=user)
    
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
    game_stats, created = UserStatistics.objects.get_or_create(user=user)
    
    # Obtener progreso del usuario
    progreso, created = Progress.objects.get_or_create(user=user)
    
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
    game_stats, created = UserStatistics.objects.get_or_create(user=user)
    
    # Obtener progreso del usuario
    progreso, created = Progress.objects.get_or_create(user=user)
    
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
            estadisticas, created = UserStatistics.objects.get_or_create(user=user)
            estadisticas.games_played += 1
            estadisticas.total_points += score
            estadisticas.total_time_played += time_taken
            estadisticas.save()
            
            # Actualizar progreso del usuario
            progreso, created = Progress.objects.get_or_create(user=user)
            progreso.current_points += score
            progreso.save()
            
            # Registrar sesión de juego
            UserGame.objects.create(
                user=user,
                game=Games.objects.get_or_create(
                    name=f"{game_type} Game",
                    defaults={'description': f'Juego de {game_type}', 'difficulty': 2}
                )[0],
                score=score,
                time_played=time_taken,
                FechaJugada=timezone.now()
            )
            
            # Verificar si sube de nivel
            nivel, created = Levels.objects.get_or_create(user=user)
            points_for_next_level = nivel.level * 100
            
            if progreso.current_points >= points_for_next_level:
                nivel.level += 1
                nivel.points_acumulados += progreso.current_points
                progreso.current_points = 0
                nivel.save()
                progreso.save()
                
                return JsonResponse({
                    'success': True,
                    'level_up': True,
                    'new_level': nivel.level,
                    'message': f'¡Felicidades! Has subido al nivel {nivel.level}'
                })
            
            return JsonResponse({
                'success': True,
                'level_up': False,
                'score': score,
                'total_points': estadisticas.total_points
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
    
    estadisticas, created = UserStatistics.objects.get_or_create(user=user)
    progreso, created = Progress.objects.get_or_create(user=user)
    nivel, created = Levels.objects.get_or_create(user=user)
    
    return JsonResponse({
        'total_games': estadisticas.games_played,
        'total_points': estadisticas.total_points,
        'current_level': nivel.level,
        'current_points': progreso.current_points,
        'points_to_next': (nivel.level * 100) - progreso.current_points
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
        classrooms = Classroom.objects.filter(teacher=request.user)
    else:  # Student
        classroom_relations = ClassroomStudent.objects.filter(student=request.user)
        classrooms = Classroom.objects.filter(id__in=classroom_relations.values_list('classroom', flat=True))
    
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
        if classroom.teacher != request.user:
            return redirect('messaging_dashboard')
    else:  # Student
        if not ClassroomStudent.objects.filter(student=request.user, classroom=classroom).exists():
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

