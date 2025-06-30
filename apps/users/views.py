from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .models import User, Class, StudentClass, StudentProgress
from .forms import StudentRegisterForm, LoginForm, TeacherRegisterForm, ParentRegisterForm
from django.contrib.auth.decorators import login_required
from apps.gamification.models import Badge, Certificate, GamifiedActivity
from django.contrib import messages
import logging
import uuid

# Vistas de login por tipo de usuario
def login_student(request):
    return login_view(request, 'accounts/login_student.html', user_type=1)

def login_teacher(request):
    return login_view(request, 'accounts/login_teacher.html', user_type=2)

def login_parent(request):
    return login_view(request, 'accounts/login_parent.html', user_type=3)

def login_admin(request):
    return login_view(request, 'accounts/login_admin.html', user_type=4)

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

# Vistas de registro por tipo de usuario
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
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('/')

# Vistas protegidas
@login_required
def dashboard_admin(request):
    logging.debug("Entrando a dashboard_admin")
    print("Entrando a dashboard_admin")
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
    return render(request, 'dashboards/dashboard_teacher.html')

@login_required
def join_class(request):
    if request.method == 'POST':
        course_code = request.POST.get('course_code')  # Corrección: Usar course_code en lugar de course_name
        if course_code:
            try:
                classroom = Class.objects.get(access_code=course_code)
                if not StudentClass.objects.filter(student=request.user, class_id=classroom).exists():
                    StudentClass.objects.create(student=request.user, class_id=classroom)
                    messages.success(request, f"Te has unido a {classroom.name} con código {course_code}.")
                else:
                    messages.error(request, "Ya estás inscrito en esta clase.")
            except Class.DoesNotExist:
                messages.error(request, "Código de clase inválido.")
        else:
            messages.error(request, "Por favor, completa todos los campos.")
    return redirect('users:dashboard_student')  # Redirigir correctamente

@login_required
def dashboard_student(request):
    user = request.user
    progress, created = StudentProgress.objects.get_or_create(user=user)
    return render(request, 'dashboards/dashboard_student.html', {
        'user_badges': progress.badges.all(),
        'user_certificates': Certificate.objects.filter(user=user),
        'user_courses': StudentClass.objects.filter(student=user),
        'pending_activities': GamifiedActivity.objects.filter(completed_by__isnull=True),
        'completed_activities': GamifiedActivity.objects.filter(completed_by=user),  # Añadir actividades completadas
        'user_courses_count': StudentClass.objects.filter(student=user).count(),
        'pending_activities_count': GamifiedActivity.objects.filter(completed_by__isnull=True).count(),
        'upcoming_events_count': 0,
        'progress': progress,
    })

@login_required
def class_teacher(request, class_id):
    classroom = Class.objects.get(id=class_id)
    if classroom.teacher != request.user:
        return redirect('users:dashboard_teacher')
    students = StudentClass.objects.filter(class_id=classroom)
    progress_list = []
    for student in students:
        progress, _ = StudentProgress.objects.get_or_create(user=student.student)
        progress_list.append({'user': student.student, 'points': progress.points})
    progress_list.sort(key=lambda x: x['points'], reverse=True)

    chat_messages = []  # Placeholder, implementar modelo de chat si es necesario

    if request.method == 'POST':
        if 'reward_student' in request.POST:
            student_id = request.POST.get('student_id')
            points = int(request.POST.get('reward_student'))
            student = User.objects.get(id=student_id)
            progress, _ = StudentProgress.objects.get_or_create(user=student)
            progress.points += points
            progress.save()
            messages.success(request, f"Se otorgaron {points} puntos a {student.username}.")
        elif 'chat_message' in request.POST:
            chat_message = request.POST.get('chat_message')
            if chat_message:
                messages.success(request, f"Mensaje enviado: {chat_message}")
        return redirect('users:class_teacher', class_id=class_id)

    return render(request, 'class/class_teacher.html', {
        'class': classroom,
        'students': students,
        'progress_list': progress_list,
        'chat_messages': chat_messages,
    })

@login_required
def class_student(request, class_id):
    classroom = Class.objects.get(id=class_id)
    if not StudentClass.objects.filter(student=request.user, class_id=classroom).exists():
        return redirect('users:dashboard_student')
    progress, _ = StudentProgress.objects.get_or_create(user=request.user)
    activities = GamifiedActivity.objects.filter(grade=classroom.grade)

    # Datos de ejemplo para theoretical_content (deberías definir un modelo si es dinámico)
    theoretical_content = [
        {'title': 'Introducción a la Biología', 'description': 'La biología es la ciencia que estudia los seres vivos...', 'file': None},
    ]

    # Datos de ejemplo para chat_messages (deberías definir un modelo de chat)
    chat_messages = []  # Placeholder, implementar modelo de chat si es necesario

    if request.method == 'POST':
        chat_message = request.POST.get('chat_message')
        if chat_message:
            # Aquí deberías guardar el mensaje en un modelo de chat (ejemplo placeholder)
            messages.success(request, f"Mensaje enviado: {chat_message}")
        return redirect('users:class_student', class_id=class_id)

    return render(request, 'class/class_student.html', {
        'class': classroom,
        'progress': progress,
        'activities': activities,
        'theoretical_content': theoretical_content,
        'chat_messages': chat_messages,
    })

@login_required
def play_game(request, class_id):
    if request.method == 'POST':
        classroom = Class.objects.get(id=class_id)
        if StudentClass.objects.filter(student=request.user, class_id=classroom).exists():
            progress, _ = StudentProgress.objects.get_or_create(user=request.user)
            points_earned = 50
            progress.points += points_earned
            progress.save()

            badges = Badge.objects.filter(points_required__lte=progress.points)
            for badge in badges:
                if not progress.badges.filter(id=badge.id).exists():
                    progress.badges.add(badge)
                    messages.success(request, f"¡Ganaste la insignia '{badge.name}'!")
            messages.success(request, f"¡Ganaste {points_earned} puntos!")
        return redirect('users:class_student', class_id=class_id)
    classroom = Class.objects.get(id=class_id)
    return render(request, 'dashboards/class_student.html', {'class': classroom})

# Vistas faltantes (placeholders)
@login_required
def create_class(request):
    if request.method == 'POST':
        name = request.POST.get('class_name')
        grade = request.POST.get('grade')
        section = request.POST.get('section')
        description = request.POST.get('description')
        access_code = request.POST.get('access_code', str(uuid.uuid4())[:8])
        if not all([name, grade, section]):
            messages.error(request, "Por favor completa todos los campos obligatorios.")
            return render(request, 'dashboards/dashboard_teacher.html')
        Class.objects.create(teacher=request.user, name=name, grade=grade, section=section, description=description, access_code=access_code)
        messages.success(request, f"Clase creada con código de acceso: {access_code}")
        return redirect('users:dashboard_teacher')
    return render(request, 'dashboards/dashboard_teacher.html')

@login_required
def remove_student(request, class_id, student_id):
    classroom = Class.objects.get(id=class_id)
    if classroom.teacher != request.user:
        return redirect('users:dashboard_teacher')
    student = User.objects.get(id=student_id)
    StudentClass.objects.filter(class_id=classroom, student=student).delete()
    messages.success(request, f"Estudiante {student.username} removido de la clase.")
    return redirect('users:class_teacher', class_id=class_id)

@login_required
def create_activity(request, class_id):
    if request.method == 'POST':
        name = request.POST.get('activity_name')
        points = request.POST.get('points', 10)
        if name:
            classroom = Class.objects.get(id=class_id)
            GamifiedActivity.objects.create(name=name, points=points, grade=classroom.grade)
            messages.success(request, f"Actividad '{name}' creada.")
        else:
            messages.error(request, "Por favor, ingresa un nombre para la actividad.")
    return redirect('users:class_teacher', class_id=class_id)