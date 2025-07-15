from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum, Max, Min
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from .models import (
    Assignment, AssignmentSubmission, CompetencyEvaluation,
    Reading, ReadingProgress,
    Test, Question, QuestionOption, TestAttempt, TestAnswer,
    Game, GameSession, ClassroomActivity
)
from apps.users.models import User
from apps.educational_games.gamification.models import Classroom

User = get_user_model()

# ============================================================================
# VISTAS DE GESTIÓN DE ACTIVIDADES (DOCENTES)
# ============================================================================

@login_required
def activity_dashboard(request):
    """Dashboard principal para gestión de actividades"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden acceder a esta página.')
        return redirect('users:dashboard_student', user_id=request.user.id)
    
    # Estadísticas del docente
    total_assignments = Assignment.objects.filter(author=request.user).count()
    total_readings = Reading.objects.filter(author=request.user).count()
    total_tests = Test.objects.filter(author=request.user).count()
    total_games = Game.objects.filter(author=request.user).count()
    
    # Actividades recientes
    recent_activities = []
    recent_assignments = Assignment.objects.filter(author=request.user).order_by('-created_at')[:5]
    recent_readings = Reading.objects.filter(author=request.user).order_by('-created_at')[:5]
    recent_tests = Test.objects.filter(author=request.user).order_by('-created_at')[:5]
    recent_games = Game.objects.filter(author=request.user).order_by('-created_at')[:5]
    
    # Aulas del docente
    classrooms = Classroom.objects.filter(teacher=request.user)
    
    context = {
        'total_assignments': total_assignments,
        'total_readings': total_readings,
        'total_tests': total_tests,
        'total_games': total_games,
        'recent_assignments': recent_assignments,
        'recent_readings': recent_readings,
        'recent_tests': recent_tests,
        'recent_games': recent_games,
        'classrooms': classrooms,
    }
    
    return render(request, 'educational_games/activity/activity_dashboard.html', context)

# ============================================================================
# VISTAS DE TAREAS
# ============================================================================

@login_required
def assignment_list(request):
    """Lista de tareas del docente"""
    if request.user.user_type != 2:
        messages.error(request, 'Solo los docentes pueden ver esta página.')
        return redirect('users:dashboard_student', user_id=request.user.id)
    
    assignments = Assignment.objects.filter(author=request.user).order_by('-created_at')
    
    # Filtros
    status = request.GET.get('status')
    if status == 'active':
        assignments = assignments.filter(is_active=True)
    elif status == 'inactive':
        assignments = assignments.filter(is_active=False)
    
    # Búsqueda
    search = request.GET.get('search')
    if search:
        assignments = assignments.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
    
    context = {
        'assignments': assignments,
        'total_assignments': assignments.count(),
        'classrooms': Classroom.objects.filter(teacher=request.user),
    }
    
    return render(request, 'educational_games/activity/assignment_list.html', context)

@login_required
def assignment_create(request):
    """Crear nueva tarea (solo si se asigna a un aula)"""
    if request.user.user_type != 2:
        messages.error(request, 'Solo los docentes pueden crear tareas.')
        return redirect('users:dashboard_student', user_id=request.user.id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        instructions = request.POST.get('instructions')
        points = request.POST.get('points', 100)
        due_date = request.POST.get('due_date')
        time_limit = request.POST.get('time_limit', 0)
        allow_late_submission = request.POST.get('allow_late_submission') == 'on'
        max_attempts = request.POST.get('max_attempts', 1)
        is_public = request.POST.get('is_public') == 'on'
        classroom_id = request.POST.get('classroom')
        if not classroom_id:
            return JsonResponse({'success': False, 'error': 'Debes seleccionar un aula para asignar la tarea.'}, status=400)
        classroom = Classroom.objects.filter(id=classroom_id, teacher=request.user).first()
        if not classroom:
            return JsonResponse({'success': False, 'error': 'Aula no válida.'}, status=400)
        assignment = Assignment.objects.create(
            title=title,
            description=description,
            instructions=instructions,
            points=points,
            due_date=due_date,
            time_limit=time_limit,
            allow_late_submission=allow_late_submission,
            max_attempts=max_attempts,
            is_public=is_public,
            author=request.user
        )
        # Manejo de adjuntos
        if request.FILES.getlist('attachments'):
            for f in request.FILES.getlist('attachments'):
                assignment.attachments.create(file=f, filename=f.name)
        ClassroomActivity.objects.create(
            classroom=classroom,
            activity_type='assignment',
            assignment=assignment,
            assigned_by=request.user
        )
        return JsonResponse({'success': True, 'assignment_id': assignment.id})
    context = {
        'classrooms': Classroom.objects.filter(teacher=request.user),
    }
    return render(request, 'educational_games/activity/assignment_create.html', context)

@login_required
def assignment_detail(request, assignment_id):
    """Detalle de una tarea"""
    assignment = get_object_or_404(Assignment, id=assignment_id, author=request.user)
    
    # Entregas de estudiantes
    submissions = AssignmentSubmission.objects.filter(assignment=assignment)
    
    # Estadísticas
    total_submissions = submissions.count()
    graded_submissions = submissions.filter(grade__isnull=False).count()
    pending_submissions = total_submissions - graded_submissions
    
    context = {
        'assignment': assignment,
        'submissions': submissions,
        'total_submissions': total_submissions,
        'graded_submissions': graded_submissions,
        'pending_submissions': pending_submissions,
    }
    
    return render(request, 'educational_games/assignments/assignment_detail.html', context)

@login_required
def assignment_edit(request, assignment_id):
    """Editar tarea"""
    assignment = get_object_or_404(Assignment, id=assignment_id, author=request.user)
    
    if request.method == 'POST':
        assignment.title = request.POST.get('title')
        assignment.description = request.POST.get('description')
        assignment.instructions = request.POST.get('instructions')
        assignment.points = request.POST.get('points', 100)
        assignment.due_date = request.POST.get('due_date')
        assignment.time_limit = request.POST.get('time_limit', 0)
        assignment.allow_late_submission = request.POST.get('allow_late_submission') == 'on'
        assignment.max_attempts = request.POST.get('max_attempts', 1)
        assignment.is_public = request.POST.get('is_public') == 'on'
        assignment.save()
        
        messages.success(request, f'Tarea "{assignment.title}" actualizada exitosamente.')
        return redirect('educational_games:assignment_detail', assignment_id=assignment.id)
    
    context = {
        'assignment': assignment,
        'classrooms': Classroom.objects.filter(teacher=request.user),
    }
    
    return render(request, 'educational_games/assignments/assignment_edit.html', context)

@login_required
def assignment_submissions(request, assignment_id):
    """Ver todas las entregas de una tarea"""
    assignment = get_object_or_404(Assignment, id=assignment_id, author=request.user)
    submissions = AssignmentSubmission.objects.filter(assignment=assignment).order_by('-submitted_at')
    
    context = {
        'assignment': assignment,
        'submissions': submissions,
    }
    
    return render(request, 'educational_games/assignments/assignment_submissions.html', context)

@login_required
def grade_submission(request, submission_id):
    """Calificar entrega de tarea"""
    submission = get_object_or_404(AssignmentSubmission, id=submission_id)
    assignment = submission.assignment
    
    # Verificar que el docente es el autor de la tarea
    if assignment.author != request.user:
        messages.error(request, 'No tienes permisos para calificar esta tarea.')
        return redirect('educational_games:assignment_submissions', assignment_id=assignment.id)
    
    if request.method == 'POST':
        grade = request.POST.get('grade')
        feedback = request.POST.get('feedback')
        
        submission.grade = grade
        submission.feedback = feedback
        submission.save()
        
        # Evaluación por competencias
        competencies = request.POST.getlist('competencies')
        competency_scores = request.POST.getlist('competency_scores')
        competency_comments = request.POST.getlist('competency_comments')
        
        # Eliminar evaluaciones anteriores
        CompetencyEvaluation.objects.filter(submission=submission).delete()
        
        # Crear nuevas evaluaciones
        for i, competency in enumerate(competencies):
            if competency and competency_scores[i]:
                CompetencyEvaluation.objects.create(
                    submission=submission,
                    competency=competency,
                    score=competency_scores[i],
                    comments=competency_comments[i] if i < len(competency_comments) else ''
                )
        
        messages.success(request, f'Entrega de {submission.student.get_full_name()} calificada exitosamente.')
        return redirect('educational_games:assignment_submissions', assignment_id=assignment.id)
    
    context = {
        'submission': submission,
        'assignment': assignment,
        'competencies': CompetencyEvaluation.COMPETENCIES,
    }
    
    return render(request, 'educational_games/assignments/grade_submission.html', context)

# ============================================================================
# VISTAS DE LECTURAS
# ============================================================================

@login_required
def reading_list(request):
    """Lista de lecturas del docente"""
    if request.user.user_type != 2:
        messages.error(request, 'Solo los docentes pueden ver esta página.')
        return redirect('users:dashboard_student', user_id=request.user.id)
    
    readings = Reading.objects.filter(author=request.user).order_by('-created_at')
    
    # Filtros
    difficulty = request.GET.get('difficulty')
    if difficulty:
        readings = readings.filter(difficulty_level=difficulty)
    
    # Búsqueda
    search = request.GET.get('search')
    if search:
        readings = readings.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
    
    context = {
        'readings': readings,
        'total_readings': readings.count(),
        'classrooms': Classroom.objects.filter(teacher=request.user),
    }
    
    return render(request, 'educational_games/activity/reading_list.html', context)

@login_required
def reading_create(request):
    """Crear nueva lectura (solo si se asigna a un aula)"""
    if request.user.user_type != 2:
        messages.error(request, 'Solo los docentes pueden crear lecturas.')
        return redirect('users:dashboard_student', user_id=request.user.id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        content = request.POST.get('content')
        difficulty = request.POST.get('difficulty')
        estimated_time = request.POST.get('estimated_time', 15)
        reading_type = request.POST.get('reading_type')
        classroom_id = request.POST.get('classroom')
        
        if not classroom_id:
            return JsonResponse({'success': False, 'error': 'Debes seleccionar un aula para asignar la lectura.'}, status=400)
        
        classroom = Classroom.objects.filter(id=classroom_id, teacher=request.user).first()
        if not classroom:
            return JsonResponse({'success': False, 'error': 'Aula no válida.'}, status=400)
        
        reading = Reading.objects.create(
            title=title,
            description=description,
            content=content,
            difficulty_level=difficulty,
            estimated_time=estimated_time,
            author=request.user
        )
        
        # Manejo de adjuntos
        if request.FILES.getlist('attachments'):
            for f in request.FILES.getlist('attachments'):
                reading.attachments.create(file=f, filename=f.name)
        
        ClassroomActivity.objects.create(
            classroom=classroom,
            activity_type='reading',
            reading=reading,
            assigned_by=request.user
        )
        
        return JsonResponse({'success': True, 'reading_id': reading.id})
    
    context = {
        'classrooms': Classroom.objects.filter(teacher=request.user),
    }
    return render(request, 'educational_games/activity/reading_create.html', context)

@login_required
def reading_detail(request, reading_id):
    """Detalle de una lectura"""
    reading = get_object_or_404(Reading, id=reading_id, author=request.user)
    
    # Progreso de estudiantes
    progress = ReadingProgress.objects.filter(reading=reading)
    
    # Estadísticas
    total_students = progress.count()
    completed_students = progress.filter(completed=True).count()
    
    context = {
        'reading': reading,
        'progress': progress,
        'total_students': total_students,
        'completed_students': completed_students,
    }
    
    return render(request, 'educational_games/readings/reading_detail.html', context)

# ============================================================================
# VISTAS DE TESTS
# ============================================================================

@login_required
def test_list(request):
    """Lista de tests del docente"""
    if request.user.user_type != 2:
        messages.error(request, 'Solo los docentes pueden ver esta página.')
        return redirect('users:dashboard_student', user_id=request.user.id)
    
    tests = Test.objects.filter(author=request.user).order_by('-created_at')
    
    # Filtros
    status = request.GET.get('status')
    if status == 'active':
        tests = tests.filter(is_active=True)
    elif status == 'inactive':
        tests = tests.filter(is_active=False)
    
    context = {
        'tests': tests,
        'total_tests': tests.count(),
        'classrooms': Classroom.objects.filter(teacher=request.user),
    }
    
    return render(request, 'educational_games/activity/test_list.html', context)

@login_required
def test_create(request):
    """Crear nuevo test (solo si se asigna a un aula)"""
    if request.user.user_type != 2:
        messages.error(request, 'Solo los docentes pueden crear tests.')
        return redirect('users:dashboard_student', user_id=request.user.id)
    
    if request.method == 'POST':
        title = request.POST.get('titulo')
        description = request.POST.get('descripcion')
        start_date = request.POST.get('fecha_inicio')
        end_date = request.POST.get('fecha_fin')
        time_limit = request.POST.get('tiempo_limite', 30)
        points_per_question = request.POST.get('puntos_por_pregunta', 10)
        is_public = request.POST.get('es_publico') == 'on'
        classroom_id = request.POST.get('classroom')
        if not classroom_id:
            return JsonResponse({'success': False, 'error': 'Debes seleccionar un aula para asignar el test.'}, status=400)
        classroom = Classroom.objects.filter(id=classroom_id, teacher=request.user).first()
        if not classroom:
            return JsonResponse({'success': False, 'error': 'Aula no válida.'}, status=400)
        test = Test.objects.create(
            title=title,
            description=description,
            time_limit=time_limit,
            points=points_per_question,
            is_public=is_public,
            author=request.user
        )
        # Procesar preguntas
        preguntas = request.POST.getlist('preguntas[]')
        tipos = request.POST.getlist('tipos_pregunta[]')
        puntos = request.POST.getlist('puntos_pregunta[]')
        for i, texto in enumerate(preguntas):
            tipo = tipos[i]
            puntaje = puntos[i]
            if tipo == 'multiple_choice' or tipo == 'opcion_multiple':
                tipo_db = 'multiple_choice'
            elif tipo == 'true_false' or tipo == 'verdadero_falso':
                tipo_db = 'true_false'
            elif tipo == 'short_answer' or tipo == 'texto_corto':
                tipo_db = 'short_answer'
            else:
                tipo_db = 'multiple_choice'
            pregunta = Question.objects.create(
                test=test,
                question_text=texto,
                question_type=tipo_db,
                points=puntaje,
                order=i+1
            )
            if tipo_db == 'multiple_choice':
                opciones = request.POST.getlist(f'opciones_{i}[]')
                correcta = request.POST.get(f'correcta_{i}')
                for j, opcion_texto in enumerate(opciones):
                    QuestionOption.objects.create(
                        question=pregunta,
                        option_text=opcion_texto,
                        is_correct=(str(j) == correcta),
                        order=j+1
                    )
            elif tipo_db == 'true_false':
                correcta = request.POST.get(f'correcta_{i}')
                QuestionOption.objects.create(
                    question=pregunta,
                    option_text='Verdadero',
                    is_correct=(correcta == 'verdadero'),
                    order=1
                )
                QuestionOption.objects.create(
                    question=pregunta,
                    option_text='Falso',
                    is_correct=(correcta == 'falso'),
                    order=2
                )
        ClassroomActivity.objects.create(
            classroom=classroom,
            activity_type='test',
            test=test,
            assigned_by=request.user
        )
        return JsonResponse({'success': True, 'test_id': test.id})
    context = {
        'classrooms': Classroom.objects.filter(teacher=request.user),
    }
    return render(request, 'educational_games/activity/test_create.html', context)

@login_required
def test_detail(request, test_id):
    """Detalle de un test"""
    test = get_object_or_404(Test, id=test_id, author=request.user)
    questions = Question.objects.filter(test=test)
    
    # Intentos de estudiantes
    attempts = TestAttempt.objects.filter(test=test)
    
    # Estadísticas
    total_attempts = attempts.count()
    completed_attempts = attempts.filter(is_completed=True).count()
    avg_score = attempts.filter(is_completed=True).aggregate(Avg('score'))['score__avg'] or 0
    
    context = {
        'test': test,
        'questions': questions,
        'attempts': attempts,
        'total_attempts': total_attempts,
        'completed_attempts': completed_attempts,
        'avg_score': round(avg_score, 2),
    }
    
    return render(request, 'educational_games/tests/test_detail.html', context)

@login_required
def test_edit(request, test_id):
    """Editar test"""
    test = get_object_or_404(Test, id=test_id, author=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        time_limit = request.POST.get('time_limit')
        points_per_question = request.POST.get('points_per_question')
        is_public = request.POST.get('is_public') == 'on'
        
        test.title = title
        test.description = description
        test.start_date = start_date
        test.end_date = end_date
        test.time_limit = time_limit
        test.points_per_question = points_per_question
        test.is_public = is_public
        test.save()
        
        messages.success(request, f'Test "{title}" actualizado exitosamente.')
        return redirect('educational_games:test_detail', test_id=test.id)
    
    context = {
        'test': test,
    }
    
    return render(request, 'educational_games/tests/test_edit.html', context)

@login_required
def test_take(request, test_id):
    """Tomar test (para estudiantes)"""
    test = get_object_or_404(Test, id=test_id)
    
    # Verificar que el estudiante está en una clase que tiene este test asignado
    student_classrooms = Classroom.objects.filter(
        classroomstudent__student=request.user
    )
    
    test_assigned = ClassroomActivity.objects.filter(
        classroom__in=student_classrooms,
        activity_type='test',
        test=test,
        is_active=True
    ).exists()
    
    if not test_assigned:
        messages.error(request, 'No tienes acceso a este test.')
        return redirect('users:dashboard_student', user_id=request.user.id)
    
    # Verificar si ya completó el test
    existing_attempt = TestAttempt.objects.filter(
        test=test,
        student=request.user,
        is_completed=True
    ).first()
    
    if existing_attempt:
        messages.warning(request, 'Ya completaste este test.')
        return redirect('educational_games:test_results', test_id=test.id)
    
    context = {
        'test': test,
        'questions': Question.objects.filter(test=test).order_by('?'),  # Orden aleatorio
    }
    
    return render(request, 'educational_games/tests/test_take.html', context)

@login_required
def test_results(request, test_id):
    """Resultados del test"""
    test = get_object_or_404(Test, id=test_id)
    
    if request.user.user_type == 2:  # Docente
        # Verificar que es el autor del test
        if test.author != request.user:
            messages.error(request, 'No tienes permisos para ver estos resultados.')
            return redirect('educational_games:test_list')
        
        attempts = TestAttempt.objects.filter(test=test)
    else:  # Estudiante
        # Verificar que el estudiante está en una clase que tiene este test asignado
        student_classrooms = Classroom.objects.filter(
            classroomstudent__student=request.user
        )
        
        test_assigned = ClassroomActivity.objects.filter(
            classroom__in=student_classrooms,
            activity_type='test',
            test=test,
            is_active=True
        ).exists()
        
        if not test_assigned:
            messages.error(request, 'No tienes acceso a este test.')
            return redirect('users:dashboard_student', user_id=request.user.id)
        
        attempts = TestAttempt.objects.filter(test=test, student=request.user)
    
    context = {
        'test': test,
        'attempts': attempts,
        'total_attempts': attempts.count(),
        'completed_attempts': attempts.filter(is_completed=True).count(),
        'avg_score': attempts.filter(is_completed=True).aggregate(Avg('score'))['score__avg'] or 0,
    }
    
    return render(request, 'educational_games/tests/test_results.html', context)

# ============================================================================
# VISTAS DE JUEGOS
# ============================================================================

@login_required
def game_list(request):
    """Lista de juegos del docente"""
    if request.user.user_type != 2:
        messages.error(request, 'Solo los docentes pueden ver esta página.')
        return redirect('users:dashboard_student', user_id=request.user.id)
    
    games = Game.objects.filter(author=request.user).order_by('-created_at')
    
    # Filtros
    game_type = request.GET.get('game_type')
    if game_type:
        games = games.filter(game_type=game_type)
    
    context = {
        'games': games,
        'total_games': games.count(),
        'game_types': Game.GAME_TYPES,
        'classrooms': Classroom.objects.filter(teacher=request.user),
    }
    
    return render(request, 'educational_games/activity/game_list.html', context)

@login_required
def game_create(request):
    """Crear nuevo juego (solo si se asigna a un aula)"""
    if request.user.user_type != 2:
        messages.error(request, 'Solo los docentes pueden crear juegos.')
        return redirect('users:dashboard_student', user_id=request.user.id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        instructions = request.POST.get('instructions')
        game_type = request.POST.get('game_type')
        difficulty = request.POST.get('difficulty')
        estimated_time = request.POST.get('estimated_time', 5)
        classroom_id = request.POST.get('classroom')
        
        if not classroom_id:
            return JsonResponse({'success': False, 'error': 'Debes seleccionar un aula para asignar el juego.'}, status=400)
        
        classroom = Classroom.objects.filter(id=classroom_id, teacher=request.user).first()
        if not classroom:
            return JsonResponse({'success': False, 'error': 'Aula no válida.'}, status=400)
        
        game = Game.objects.create(
            title=title,
            description=description,
            instructions=instructions,
            game_type=game_type,
            difficulty_level=difficulty,
            estimated_time=estimated_time,
            author=request.user
        )
        
        # Manejo de adjuntos
        if request.FILES.getlist('attachments'):
            for f in request.FILES.getlist('attachments'):
                game.attachments.create(file=f, filename=f.name)
        
        ClassroomActivity.objects.create(
            classroom=classroom,
            activity_type='game',
            game=game,
            assigned_by=request.user
        )
        
        return JsonResponse({'success': True, 'game_id': game.id})
    
    context = {
        'classrooms': Classroom.objects.filter(teacher=request.user),
    }
    return render(request, 'educational_games/activity/game_create.html', context)

@login_required
def game_detail(request, game_id):
    """Detalle de un juego"""
    game = get_object_or_404(Game, id=game_id, author=request.user)
    
    # Sesiones de estudiantes
    sessions = GameSession.objects.filter(game=game)
    
    # Estadísticas
    total_sessions = sessions.count()
    completed_sessions = sessions.filter(is_completed=True).count()
    avg_score = sessions.filter(is_completed=True).aggregate(Avg('score'))['score__avg'] or 0
    
    context = {
        'game': game,
        'sessions': sessions,
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'avg_score': round(avg_score, 2),
    }
    
    return render(request, 'educational_games/games/game_detail.html', context)

# ============================================================================
# VISTAS DE ASIGNACIÓN A CLASES
# ============================================================================

@login_required
def assign_activity_to_classroom(request, activity_type, activity_id):
    """Asignar actividad a una clase"""
    if request.user.user_type != 2:
        messages.error(request, 'Solo los docentes pueden asignar actividades.')
        return redirect('users:dashboard_student', user_id=request.user.id)
    
    if request.method == 'POST':
        classroom_id = request.POST.get('classroom')
        due_date = request.POST.get('due_date')
        
        classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
        
        # Obtener la actividad según el tipo
        activity = None
        if activity_type == 'assignment':
            activity = get_object_or_404(Assignment, id=activity_id, author=request.user)
        elif activity_type == 'reading':
            activity = get_object_or_404(Reading, id=activity_id, author=request.user)
        elif activity_type == 'test':
            activity = get_object_or_404(Test, id=activity_id, author=request.user)
        elif activity_type == 'game':
            activity = get_object_or_404(Game, id=activity_id, author=request.user)
        
        # Crear la asignación
        classroom_activity = ClassroomActivity.objects.create(
            classroom=classroom,
            activity_type=activity_type,
            assignment=activity if activity_type == 'assignment' else None,
            reading=activity if activity_type == 'reading' else None,
            test=activity if activity_type == 'test' else None,
            game=activity if activity_type == 'game' else None,
            assigned_by=request.user,
            due_date=due_date if due_date else None
        )
        
        messages.success(request, f'Actividad asignada exitosamente a {classroom.name}.')
        return redirect('users:class_teacher', class_id=classroom.id)
    
    # Obtener la actividad
    activity = None
    if activity_type == 'assignment':
        activity = get_object_or_404(Assignment, id=activity_id, author=request.user)
    elif activity_type == 'reading':
        activity = get_object_or_404(Reading, id=activity_id, author=request.user)
    elif activity_type == 'test':
        activity = get_object_or_404(Test, id=activity_id, author=request.user)
    elif activity_type == 'game':
        activity = get_object_or_404(Game, id=activity_id, author=request.user)
    
    context = {
        'activity': activity,
        'activity_type': activity_type,
        'classrooms': Classroom.objects.filter(teacher=request.user),
    }
    
    return render(request, 'educational_games/assign_activity.html', context)

# ============================================================================
# VISTAS DE ESTUDIANTES
# ============================================================================

@login_required
def student_assignments(request):
    """Tareas asignadas al estudiante"""
    if request.user.user_type != 3:  # Solo estudiantes
        messages.error(request, 'Solo los estudiantes pueden ver esta página.')
        return redirect('users:dashboard_teacher', user_id=request.user.id)
    
    # Obtener aulas del estudiante
    student_classrooms = Classroom.objects.filter(
        classroomstudent__student=request.user
    )
    
    # Obtener tareas asignadas
    assignments = []
    for classroom in student_classrooms:
        classroom_assignments = ClassroomActivity.objects.filter(
            classroom=classroom,
            activity_type='assignment',
            is_active=True
        )
        for ca in classroom_assignments:
            if ca.assignment:
                assignments.append(ca.assignment)
    
    context = {
        'assignments': assignments,
    }
    
    return render(request, 'educational_games/student/assignments.html', context)

@login_required
def submit_assignment(request, assignment_id):
    """Entregar tarea"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    # Verificar que el estudiante está en una clase que tiene esta tarea asignada
    student_classrooms = Classroom.objects.filter(
        classroomstudent__student=request.user
    )
    
    has_access = ClassroomActivity.objects.filter(
        classroom__in=student_classrooms,
        activity_type='assignment',
        assignment=assignment,
        is_active=True
    ).exists()
    
    if not has_access:
        messages.error(request, 'No tienes acceso a esta tarea.')
        return redirect('educational_games:student_assignments')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        file = request.FILES.get('file')
        
        # Verificar si ya existe una entrega
        existing_submission = AssignmentSubmission.objects.filter(
            assignment=assignment,
            student=request.user
        ).first()
        
        if existing_submission:
            attempt_number = existing_submission.attempt_number + 1
        else:
            attempt_number = 1
        
        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            student=request.user,
            content=content,
            file=file,
            attempt_number=attempt_number
        )
        
        messages.success(request, 'Tarea entregada exitosamente.')
        return redirect('educational_games:student_assignments') 
 
 
@csrf_exempt
@login_required
def assignment_create_api(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    title = request.POST.get('title')
    description = request.POST.get('description')
    instructions = request.POST.get('instructions')
    due_date = request.POST.get('due_date')
    is_public = request.POST.get('is_public') == 'on'
    assignment = Assignment.objects.create(
        title=title,
        description=description,
        instructions=instructions,
        due_date=due_date,
        author=request.user,
        is_public=is_public
    )
    return JsonResponse({'success': True, 'assignment_id': assignment.id})

@csrf_exempt
@login_required
def assignment_edit_api(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, author=request.user)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    assignment.title = request.POST.get('title', assignment.title)
    assignment.description = request.POST.get('description', assignment.description)
    assignment.instructions = request.POST.get('instructions', assignment.instructions)
    assignment.due_date = request.POST.get('due_date', assignment.due_date)
    assignment.is_public = request.POST.get('is_public') == 'on'
    assignment.save()
    return JsonResponse({'success': True})

@csrf_exempt
@login_required
def assignment_delete_api(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, author=request.user)
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    assignment.delete()
    return JsonResponse({'success': True})

@csrf_exempt
@login_required
def assignment_assign_classes_api(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, author=request.user)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    ids = request.POST.getlist('classroom_ids')
    ClassroomActivity.objects.filter(assignment=assignment).delete()
    for cid in ids:
        classroom = Classroom.objects.filter(id=cid, teacher=request.user).first()
        if classroom:
            ClassroomActivity.objects.create(
                classroom=classroom,
                activity_type='assignment',
                assignment=assignment,
                assigned_by=request.user
            )
    return JsonResponse({'success': True})

@login_required
def assignment_public_list_api(request):
    assignments = Assignment.objects.filter(is_public=True).order_by('-created_at')
    data = [{'id': a.id, 'title': a.title, 'description': a.description} for a in assignments]
    return JsonResponse({'assignments': data})
 
 