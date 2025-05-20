from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, ParentProfile

class StudentRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(label='Nombres', required=True)
    last_name = forms.CharField(label='Apellido Paterno y Materno', required=True)
    school = forms.CharField(label='Institución educativa', required=False)
    nivel= forms.CharField(label='Nivel educativo', required=False)
    grade = forms.CharField(label='Grado de nivel educativo', required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'school', 'grade')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 1
        if commit:
            user.save()
        return user

class TeacherRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(label='Nombres', required=True)
    last_name = forms.CharField(label='Apellidos', required=True)
    school = forms.CharField(label='Institución educativa', required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'school')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 2
        if commit:
            user.save()
        return user

class ParentRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(label='Nombres', required=True)
    last_name = forms.CharField(label='Apellidos', required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

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
