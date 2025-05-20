from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import User
from .forms import StudentRegisterForm
from django.contrib.auth.decorators import login_required   
from .forms import LoginForm, TeacherRegisterForm, ParentRegisterForm

def login_student(request):
    return login_view(request, 'accounts/login_student.html', user_type=1)

def login_teacher(request):
    return login_view(request, 'accounts/login_teacher.html', user_type=2)

def login_parent(request):
    return login_view(request, 'accounts/login_parent.html', user_type=3)

def login_admin(request):
    return login_view(request, 'accounts/login_admin.html', user_type=4)

def login_view(request, template, user_type):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.user_type == user_type:
                login(request, user)
                return redirect('accounts:dashboard')
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
def dashboard(request):
    dashboard_templates = {
        1: 'dashboards/dashboard_student.html',
        2: 'dashboards/dashboard_teacher.html',
        3: 'dashboards/dashboard_parent.html',
        4: 'dashboards/dashboard_admin.html',
    }
    user_type = getattr(request.user, 'user_type', None)
    template = dashboard_templates.get(user_type)
    if template:
        return render(request, template)
    else:
        return render(request, 'error.html', {'message': 'Tipo de usuario no definido.'})
    
