from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, ParentProfile

class StudentRegisterForm(UserCreationForm):
    
    email = forms.EmailField(label='Correo electrónico', required=True,
        error_messages={
            'required': 'Este campo es obligatorio.',
            'invalid': 'Ingresa una dirección de correo válida.',
        }
    )
    
    first_name = forms.CharField(label='Nombres', required=True, max_length=30,
        error_messages={
            'required': 'Este campo es obligatorio.',
            'max_length': 'Asegúrate de que este valor tenga como máximo 30 caracteres.',
        }
    )
    
    last_name = forms.CharField(label='Apellido Paterno y Materno', required=True, max_length=30,
        error_messages={
            'required': 'Este campo es obligatorio.',
            'max_length': 'Asegúrate de que este valor tenga como máximo 30 caracteres.',
        }
    )
    
    school = forms.CharField(label='Institución educativa', required=False, max_length=100,
        error_messages={
            'max_length': 'Asegúrate de que este valor tenga como máximo 100 caracteres.',
        }
    )
    
    nivel = forms.CharField(label='Nivel educativo', required=False, max_length=50)
    
    grade = forms.CharField(label='Grado de nivel educativo', required=False, max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'list': 'grade-options',
            'autocomplete': 'off'
        }),
        error_messages={
            'max_length': 'Asegúrate de que este valor tenga como máximo 50 caracteres.',
        }
    )
    
    username = forms.CharField(
        label='Nombre de usuario',
        max_length=20,
        error_messages={
            'required': 'Este campo es obligatorio.',
            'max_length': 'Asegúrate de que este valor tenga como máximo 20 caracteres.',
            'invalid': 'Ingresa un nombre de usuario válido.',
        }
    )
    
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput,
        help_text='Debe contener al menos 8 caracteres.',
        error_messages={
            'required': 'Este campo es obligatorio.',
        }
    )
    
    password2 = forms.CharField(
        label='Repetir contraseña',
        widget=forms.PasswordInput,
        help_text='Ingrese la misma contraseña para verificación.',
        error_messages={
            'required': 'Este campo es obligatorio.',
        }
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'school', 'grade')
        labels = {
            'username': 'Nombre de usuario',
        }
        error_messages = {
            'username': {
                'unique': 'Ya existe un usuario con este nombre.',
                'max_length': 'Asegúrate de que este valor tenga como máximo 20 caracteres.',
            },
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) > 20:
            raise ValidationError('Asegúrate de que este valor tenga como máximo 20 caracteres.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Ya existe un usuario con este correo electrónico.')
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                raise ValidationError('Las contraseñas no coinciden.')
            
            username = self.cleaned_data.get('username')
            if username and password1.lower() in username.lower():
                raise ValidationError('La contraseña es muy similar al nombre de usuario.')
                
        return password2

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