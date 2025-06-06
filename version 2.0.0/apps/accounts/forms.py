from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, ParentProfile

class StudentRegisterForm(UserCreationForm):
    GRADE_CHOICES = [
        ('', 'Selecciona tu grado'),
        ('primero', 'Primero'),
        ('segundo', 'Segundo'),
    ]
    email = forms.EmailField(label='Correo electrónico', required=True)
    first_name = forms.CharField(label='Nombres', required=True)
    last_name = forms.CharField(label='Apellido Paterno y Materno', required=True)
    school = forms.CharField(label='Institución educativa', required=False)
    nivel = forms.CharField(label='Nivel educativo', required=False)
    grade = forms.CharField(label='Grado de nivel educativo', required=False)
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput,
        help_text='Debe contener al menos 8 caracteres.'
    )
    password2 = forms.CharField(
        label='Repetir contraseña',
        widget=forms.PasswordInput,
        help_text='Ingrese la misma contraseña para verificación.'
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'school', 'grade')
        labels = {
            'username': 'Nombre de usuario',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 1
        if commit:
            user.save()
        return user

class TeacherRegisterForm(UserCreationForm):
    email = forms.EmailField(label='Correo electrónico', required=True)
    first_name = forms.CharField(label='Nombres', required=True)
    last_name = forms.CharField(label='Apellidos', required=True)
    school = forms.CharField(label='Institución educativa', required=True)
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput,
        help_text='Debe contener al menos 8 caracteres.'
    )
    password2 = forms.CharField(
        label='Repetir contraseña',
        widget=forms.PasswordInput,
        help_text='Ingrese la misma contraseña para verificación.'
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'school')
        labels = {
            'username': 'Nombre de usuario',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 2
        if commit:
            user.save()
        return user

class ParentRegisterForm(UserCreationForm):
    email = forms.EmailField(label='Correo electrónico', required=True)
    first_name = forms.CharField(label='Nombres', required=True)
    last_name = forms.CharField(label='Apellidos', required=True)
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput,
        help_text='Debe contener al menos 8 caracteres.'
    )
    password2 = forms.CharField(
        label='Repetir contraseña',
        widget=forms.PasswordInput,
        help_text='Ingrese la misma contraseña para verificación.'
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        labels = {
            'username': 'Nombre de usuario',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 3
        if commit:
            user.save()
            ParentProfile.objects.create(user=user)
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Usuario o correo')
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)