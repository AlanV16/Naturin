from django.shortcuts import render, redirect
from django.contrib.auth import login
from .models import User
from .forms import StudentRegisterForm
from django.contrib.auth.decorators import login_required
from .forms import LoginForm, TeacherRegisterForm, ParentRegisterForm
import logging

# Vistas existentes...
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
                    return redirect('accounts:dashboard_student')
                elif user_type == 2:
                    return redirect('accounts:dashboard_teacher')
                elif user_type == 3:
                    return redirect('accounts:dashboard_parent')
                elif user_type == 4:
                    return redirect('accounts:dashboard_admin')
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
            return redirect('accounts:login_student')
    else:
        form = form_class()
    return render(request, template, {'form': form})

@login_required
def dashboard_student(request):
    return render(request, 'dashboards/dashboard_student.html')

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

# Nuevas vistas básicas
@login_required
def home(request):
    return render(request, 'accounts/home.html')  # Crea un template 'home.html'

@login_required
def courses(request):
    return render(request, 'accounts/courses.html')  # Crea un template 'courses.html'

@login_required
def grades(request):
    return render(request, 'accounts/grades.html') 

@login_required
def messages(request):
    return render(request, 'accounts/messages.html')

@login_required
def join_class(request):
    if request.method == 'POST':
        # Lógica para unir a una clase (ejemplo)
        course_name = request.POST.get('course_name')
        course_code = request.POST.get('course_code')
        # Aquí deberías validar y guardar la inscripción
        return redirect('accounts:dashboard_student')
    return render(request, 'accounts/join_class.html')  # Opcional, template para el formulario

@login_required
def course_detail(request, course_id):
    # Lógica para mostrar detalles del curso
    return render(request, 'accounts/course_detail.html', {'course_id': course_id})  # Crea un template 'course_detail.html'