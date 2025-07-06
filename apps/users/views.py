from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .models import User
from .forms import StudentRegisterForm, TeacherRegisterForm, ParentRegisterForm, LoginForm
from django.contrib.auth.decorators import login_required   
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import login
import logging
import random
import string
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone

# Importar modelos de gamificación
from apps.educational_games.gamification.models import (
    Aulas, AulaEstudiante, Actividades, Niveles
)

def login_student(request):
    return login_view(request, 'accounts/login_student.html', user_type=1)

def login_teacher(request):
    return login_view(request, 'accounts/login_teacher.html', user_type=2)

def login_parent(request):
    return login_view(request, 'accounts/login_parent.html', user_type=3)

def login_admin(request):
    return login_view(request, 'accounts/login_admin.html', user_type=4)

from django.contrib.auth import login

def login_view(request, template, user_type):
    print(f"[DEBUG] user_type esperado desde la vista: {user_type}")
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            print(f"[DEBUG] Usuario autenticado: {user.username}, tipo real: {user.user_type}")
            
            if user.user_type == user_type:
                login(request, user)
                if user_type == 1:
                    return redirect('users:dashboard_student')
                elif user_type == 2:
                    return redirect('users:dashboard_teacher')
                elif user_type == 3:
                    return redirect('users:dashboard_parent')
                elif user_type == 4:
                    return redirect('users:dashboard_admin')
            else:
                form.add_error(None, "Tipo de usuario incorrecto para este acceso.")
    else:
        form = LoginForm()

    return render(request, template, {'form': form})


def register_student(request):
    return register_view(request, StudentRegisterForm, 'accounts/signup_student.html')

def register_teacher(request):
    return register_view(request, TeacherRegisterForm, 'accounts/signup_teacher.html')

def register_parent(request):
    return register_view(request, ParentRegisterForm, 'accounts/signup_parent.html')

def register_view(request, form_class, template):
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            form.save()
            return redirect('users:login_student')
    else:
        form = form_class()
    return render(request, template, {'form': form})

def logout_view(request):
    """Vista personalizada de logout que acepta GET y POST"""
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('users:login_student')

@login_required
def dashboard_student(request):
    # Obtener clases del estudiante
    student_classes = AulaEstudiante.objects.filter(IDestudiante=request.user)
    
    # Obtener progreso del estudiante
    try:
        progress = Niveles.objects.get(IDusuario=request.user)
    except Niveles.DoesNotExist:
        progress = None
    
    context = {
        'student_classes': student_classes,
        'total_classes': student_classes.count(),
        'progress': progress,
    }
    
    return render(request, 'dashboards/dashboard_student.html', context)
@login_required
def dashboard_admin(request):
    logging.debug("Entrando a dashboard_admin")
    print("Entrando a dashboard_admin")  # para la consola de runserver
    return render(request, 'dashboards/dashboard_admin.html')
@login_required
def dashboard_parent(request):
    logging.debug("Entrando a dashboard_parent")
    print("Entrando a dashboard_parent")
    return render(request, 'dashboards/dashboard_parent.html')
@login_required
def dashboard_teacher(request):
    logging.debug("Entrando a dashboard_teacher")
    print("Entrando a dashboard_teacher")
    
    # Obtener clases del docente
    teacher_classes = Aulas.objects.filter(IDdocente=request.user)
    
    # Contar estudiantes totales
    total_students = 0
    for classroom in teacher_classes:
        total_students += AulaEstudiante.objects.filter(IDaula=classroom).count()
    
    # Obtener recursos creados por el docente
    from apps.educational_games.gamification.models import Test
    from apps.pedagogical_guides.models import Guide
    from apps.multimedia.models import MultimediaCard
    
    # Tests creados por el docente
    tests = Test.objects.filter(IDdocente=request.user).order_by('-fecha_creacion')
    
    # Guías pedagógicas creadas por el docente
    guias = Guide.objects.filter(author=request.user).order_by('-created_at')
    
    # Recursos multimedia creados por el docente
    multimedia = MultimediaCard.objects.filter(author=request.user).order_by('-created_at')
    
    context = {
        'teacher_classes': teacher_classes,
        'total_students': total_students,
        'total_classes': teacher_classes.count(),
        'tests': tests,
        'guias': guias,
        'multimedia': multimedia,
    }
    
    return render(request, 'dashboards/dashboard_teacher.html', context)

# ============================================================================
# AULAS VIRTUALES
# ============================================================================

@login_required
def join_class(request):
    """Vista para que estudiantes se unan a una clase"""
    if request.method == 'POST':
        class_code = request.POST.get('class_code')
        
        if not class_code:
            messages.error(request, 'Por favor ingresa el código de la clase.')
            return redirect('users:dashboard_student')
        
        try:
            # Buscar la clase solo por código
            classroom = Aulas.objects.get(CodigoAula=class_code)
            
            # Verificar si el estudiante ya está en la clase
            if AulaEstudiante.objects.filter(IDaula=classroom, IDestudiante=request.user).exists():
                messages.warning(request, 'Ya estás inscrito en esta clase.')
                return redirect('users:dashboard_student')
            
            # Inscribir al estudiante
            AulaEstudiante.objects.create(
                IDaula=classroom,
                IDestudiante=request.user,
                DenominacionAula=classroom.NombreAula
            )
            
            messages.success(request, f'Te has unido exitosamente a la clase "{classroom.NombreAula}"')
            return redirect('users:class_student', class_id=classroom.IDaula)
            
        except Aulas.DoesNotExist:
            messages.error(request, 'No se encontró la clase con el código proporcionado.')
        except Exception as e:
            messages.error(request, 'Error al unirse a la clase.')
    
    # Si es GET, redirigir al dashboard
    return redirect('users:dashboard_student')

@login_required
def create_class(request):
    """Vista para que docentes creen una nueva clase"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'No tienes permisos para crear clases.')
        return redirect('users:dashboard_teacher')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Usar el código generado por JavaScript
                code = request.POST.get('class_code')
                if not code:
                    messages.error(request, 'Código de clase requerido.')
                    return redirect('users:create_class')
                
                # Crear la clase
                classroom = Aulas.objects.create(
                    NombreAula=request.POST.get('class_name'),
                    Descripcion=request.POST.get('description'),
                    GradoEducativo=request.POST.get('grade'),
                    Seccion=request.POST.get('section'),
                    CodigoAula=code,
                    IDdocente=request.user,
                    FechaCreacion=timezone.now()
                )
                
                # Asignar actividades seleccionadas
                selected_activities = request.POST.getlist('activities')
                for activity_id in selected_activities:
                    try:
                        activity = Actividades.objects.get(IDactividad=activity_id)
                        # Aquí podrías crear una relación entre la clase y la actividad
                        # Por ahora solo registramos que se seleccionó
                        pass
                    except Actividades.DoesNotExist:
                        pass
                
                messages.success(request, f'Clase "{classroom.NombreAula}" creada exitosamente.')
                return redirect('users:class_teacher', class_id=classroom.IDaula)
                
        except Exception as e:
            messages.error(request, 'Error al crear la clase.')
    
    # Obtener actividades disponibles (sin filtrar por estado ya que no existe ese campo)
    activities = Actividades.objects.all()
    
    context = {
        'activities': activities,
        'grades': ['Primero', 'Segundo'],
        'sections': ['A', 'B', 'C', 'D', 'E'],
    }
    
    return render(request, 'users/create_class.html', context)

@login_required
def class_student(request, class_id):
    """Vista de clase para estudiantes"""
    classroom = get_object_or_404(Aulas, IDaula=class_id)
    
    # Verificar si el estudiante está inscrito
    if not AulaEstudiante.objects.filter(IDaula=classroom, IDestudiante=request.user).exists():
        messages.error(request, 'No tienes acceso a esta clase.')
        return redirect('users:dashboard_student')
    
    # Obtener actividades de la clase
    activities = Actividades.objects.all()[:5]  # Limitamos a 5 por ahora
    
    # Obtener progreso del estudiante
    try:
        progress = Niveles.objects.get(IDusuario=request.user)
    except Niveles.DoesNotExist:
        progress = None
    
    # Obtener mensajes del chat (simulado por ahora)
    chat_messages = []
    
    context = {
        'class': classroom,
        'activities': activities,
        'progress': progress,
        'chat_messages': chat_messages,
        'theoretical_content': [],  # Por ahora vacío
    }
    
    return render(request, 'users/class_student.html', context)

@login_required
def class_teacher(request, class_id):
    """Vista de clase para docentes"""
    classroom = get_object_or_404(Aulas, IDaula=class_id, IDdocente=request.user)
    
    if request.method == 'POST':
        # Manejar mensajes del chat
        if 'chat_message' in request.POST:
            message = request.POST.get('chat_message')
            # Aquí guardarías el mensaje en la base de datos
            messages.success(request, 'Mensaje enviado.')
        
        # Manejar recompensas a estudiantes
        if 'reward_student' in request.POST:
            student_id = request.POST.get('student_id')
            points = int(request.POST.get('reward_student'))
            
            try:
                student = User.objects.get(id=student_id)
                nivel, created = Niveles.objects.get_or_create(IDusuario=student)
                nivel.puntos_acumulados += points
                nivel.actualizar_nivel()
                nivel.save()
                
                messages.success(request, f'Se otorgaron {points} puntos al estudiante.')
            except Exception as e:
                messages.error(request, 'Error al otorgar puntos.')
    
    # Obtener estudiantes inscritos
    students = AulaEstudiante.objects.filter(IDaula=classroom)
    
    # Obtener actividades de la clase
    activities = Actividades.objects.all()[:5]
    
    # Obtener progreso de estudiantes
    progress_list = []
    for student in students:
        try:
            nivel = Niveles.objects.get(IDusuario=student.IDestudiante)
            progress_list.append({
                'user': student.IDestudiante,
                'points': nivel.puntos_acumulados
            })
        except Niveles.DoesNotExist:
            pass
    
    # Ordenar por puntos
    progress_list.sort(key=lambda x: x['points'], reverse=True)
    
    # Obtener mensajes del chat (simulado)
    chat_messages = []
    
    context = {
        'class': classroom,
        'students': students,
        'activities': activities,
        'progress_list': progress_list,
        'chat_messages': chat_messages,
    }
    
    return render(request, 'users/class_teacher.html', context)

@login_required
def play_game(request, class_id):
    """Vista para jugar juegos educativos"""
    classroom = get_object_or_404(Aulas, IDaula=class_id)
    
    # Verificar acceso
    if request.user.user_type == 1:  # Estudiante
        if not AulaEstudiante.objects.filter(IDaula=classroom, IDestudiante=request.user).exists():
            messages.error(request, 'No tienes acceso a esta clase.')
            return redirect('users:dashboard_student')
    elif request.user.user_type == 2:  # Docente
        if classroom.IDdocente != request.user:
            messages.error(request, 'No tienes acceso a esta clase.')
            return redirect('users:dashboard_teacher')
    
    # Redirigir al sistema de gamificación
    return redirect('gamification:dashboard')