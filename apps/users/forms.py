from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User, ParentProfile
from validate_email import validate_email
from .utils import send_verification_email
from .validators import validate_teacher_email, get_allowed_teacher_domains
class StudentRegisterForm(UserCreationForm):
    GRADE_CHOICES = [
        ('', 'Selecciona tu grado'),
        ('primero', 'Primero'),
        ('segundo', 'Segundo'),
    ]

    email = forms.EmailField(label='Correo electrónico', required=True)
    first_name = forms.CharField(label='Nombres', required=True)
    last_name = forms.CharField(label='Apellido Paterno y Materno', required=True)
    school = forms.CharField(
        label='Institución educativa',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Nombre de tu colegio'})
    )
    grade = forms.ChoiceField(
        label='Grado de nivel educativo',
        choices=GRADE_CHOICES,
        required=False
    )
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
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'password1', 'password2', 'school', 'grade'
        )
        labels = {
            'username': 'Nombre de usuario',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("❌ Ya existe un usuario con este correo electrónico.")
        if not validate_email(email):
            raise ValidationError("❌ El formato del correo electrónico no es válido.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("❌ Este nombre de usuario ya está en uso.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.user_type = 1  # Estudiante
        user.school = self.cleaned_data.get('school', '')
        user.grade = self.cleaned_data.get('grade', '')
        user.is_active = False  # Requiere verificación de email
        
        if commit:
            user.save()
            # Intentar enviar email, pero no fallar si hay error
            try:
                send_verification_email(user)
            except Exception as e:
                print(f"Error enviando email: {e}")
                # Continuar sin fallar
                pass
        return user


class TeacherRegisterForm(UserCreationForm):
    email = forms.EmailField(
        label='Correo electrónico institucional', 
        required=True,
        help_text='Debe ser un email de institución educativa (ej: @unas.edu.pe, @minedu.edu.pe)'
    )
    first_name = forms.CharField(label='Nombres', required=True)
    last_name = forms.CharField(label='Apellidos', required=True)
    school = forms.CharField(
        label='Institución educativa', 
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Nombre de tu institución'})
    )
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
        fields = (
            'username', 'first_name', 'last_name',
            'email', 'password1', 'password2', 'school'
        )
        labels = {
            'username': 'Nombre de usuario',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # Verificar si ya existe un usuario con este email
        if User.objects.filter(email=email).exists():
            raise ValidationError("❌ Ya existe un usuario con este correo electrónico.")
        
        # Validar formato del email
        if not validate_email(email):
            raise ValidationError("❌ El formato del correo electrónico no es válido.")
        
        # Validar dominio institucional para docentes
        try:
            validate_teacher_email(email)
        except ValidationError as e:
            raise ValidationError(f"❌ {str(e)}")
        
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("❌ Este nombre de usuario ya está en uso.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.user_type = 2  # Docente
        user.school = self.cleaned_data.get('school', '')
        user.is_active = False
        
        if commit:
            user.save()
            # Intentar enviar email, pero no fallar si hay error
            try:
                send_verification_email(user)
            except Exception as e:
                print(f"Error enviando email: {e}")
                pass
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

    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # Verificar si ya existe un usuario con este email
        if User.objects.filter(email=email).exists():
            raise ValidationError("❌ Ya existe un usuario con este correo electrónico.")
        
        # Validar formato del email
        if not validate_email(email):
            raise ValidationError("❌ El formato del correo electrónico no es válido.")
        
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("❌ Este nombre de usuario ya está en uso.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.user_type = 3  # Tipo padre
        user.is_active = False  # Requiere verificación de email
        
        if commit:
            user.save()
            ParentProfile.objects.create(user=user)
            # Intentar enviar email, pero no fallar si hay error
            try:
                send_verification_email(user)
            except Exception as e:
                print(f"Error enviando email: {e}")
                pass
            
        return user


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Correo o nombre de usuario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu email o nombre de usuario'
        })
    )
    password = forms.CharField(
        label='Contraseña', 
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña'
        })
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        from django.contrib.auth import authenticate
        username_or_email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username_or_email and password:
            from django.contrib.auth import get_user_model
            User = get_user_model()

            try:
                # Buscar por email
                user = User.objects.get(email=username_or_email)
                username = user.username
            except User.DoesNotExist:
                username = username_or_email

            self.user_cache = authenticate(self.request, username=username, password=password)

            if self.user_cache is None:
                raise ValidationError("❌ Credenciales inválidas. Verifica tu email/usuario y contraseña.")
        
            if not self.user_cache.is_active:
                raise ValidationError("❌ Tu cuenta está desactivada. Si eres docente, verifica tu email primero.")

            # Solo validar dominio institucional para docentes si ya están verificados
            # if self.user_cache.user_type == 2 and self.user_cache.is_email_verified:  # Docente verificado
            #     dominio = self.user_cache.email.split('@')[-1].lower()
            #     dominios_permitidos = ['minedu.edu.pe', 'ugel.edu.pe', 'dre.edu.pe', 'gmail.com']  # Agregamos gmail para pruebas
            #     if dominio not in dominios_permitidos:
            #         raise ValidationError("❌ Los docentes deben usar un correo institucional.")
        
        return self.cleaned_data


    def get_user(self):
        return self.user_cache


# Formulario para cambio de contraseña personalizado
class CustomPasswordChangeForm(forms.Form):
    """
    Formulario personalizado para cambio de contraseña
    """
    old_password = forms.CharField(
        label='Contraseña actual',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password1 = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Debe contener al menos 8 caracteres.'
    )
    new_password2 = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError("❌ La contraseña actual es incorrecta.")
        return old_password

    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get('new_password1')
        new_password2 = self.cleaned_data.get('new_password2')
        
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise ValidationError("❌ Las contraseñas no coinciden.")
        
        return new_password2

    def save(self):
        new_password = self.cleaned_data['new_password1']
        self.user.set_password(new_password)
        self.user.save()
        return self.user
    
    
class EmailVerificationForm(forms.Form):
    """Formulario para verificar código de email"""
    verification_code = forms.CharField(
        label='Código de verificación',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '123456',
            'autocomplete': 'off',
            'style': 'letter-spacing: 0.5rem; font-size: 1.5rem;'
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_verification_code(self):
        code = self.cleaned_data.get('verification_code')
        
        if not code:
            raise ValidationError("❌ Por favor ingresa el código de verificación.")
        
        if not self.user.is_verification_code_valid(code):
            raise ValidationError("❌ El código es inválido o ha expirado. Solicita uno nuevo.")
        
        return code


# ================== FORMULARIOS PARA RESET DE CONTRASEÑA ==================

class PasswordResetRequestForm(forms.Form):
    """Formulario para solicitar reset de contraseña"""
    email = forms.EmailField(
        label='Correo electrónico',
        help_text='Ingresa el email asociado a tu cuenta',
        widget=forms.EmailInput(attrs={
            'placeholder': 'ejemplo@correo.com',
            'class': 'form-control'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                raise ValidationError("❌ Esta cuenta está desactivada.")
        except User.DoesNotExist:
            raise ValidationError("❌ No existe una cuenta asociada a este correo electrónico.")
        return email

    def get_user(self):
        email = self.cleaned_data.get('email')
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None


class PasswordResetVerifyForm(forms.Form):
    """Formulario para verificar código de reset"""
    reset_code = forms.CharField(
        label='Código de verificación',
        max_length=6,
        min_length=6,
        help_text='Ingresa el código de 6 dígitos que recibiste por email',
        widget=forms.TextInput(attrs={
            'placeholder': '123456',
            'class': 'form-control code-input',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'autocomplete': 'off'
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_reset_code(self):
        code = self.cleaned_data.get('reset_code')
        
        if not code:
            raise ValidationError("❌ Por favor ingresa el código de verificación.")
        
        if not code.isdigit() or len(code) != 6:
            raise ValidationError("❌ El código debe tener exactamente 6 dígitos.")
        
        if not self.user:
            raise ValidationError("❌ Usuario no válido.")
        
        if not self.user.is_password_reset_code_valid(code):
            raise ValidationError("❌ El código es inválido o ha expirado. Solicita uno nuevo.")
        
        return code


class PasswordResetForm(forms.Form):
    """Formulario para establecer nueva contraseña"""
    new_password1 = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Mínimo 8 caracteres',
            'class': 'form-control'
        }),
        help_text='Debe contener al menos 8 caracteres.'
    )
    new_password2 = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Repite la nueva contraseña',
            'class': 'form-control'
        }),
        help_text='Ingrese la misma contraseña para verificación.'
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        
        if not password:
            raise ValidationError("❌ La contraseña es obligatoria.")
        
        if len(password) < 8:
            raise ValidationError("❌ La contraseña debe tener al menos 8 caracteres.")
        
        # Validaciones adicionales de contraseña
        if password.isdigit():
            raise ValidationError("❌ La contraseña no puede ser solo números.")
        
        if password.lower() in ['password', '12345678', 'qwerty', 'abc123']:
            raise ValidationError("❌ Esta contraseña es demasiado común.")
        
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError("❌ Las contraseñas no coinciden.")

        return cleaned_data

    def save(self):
        """Actualiza la contraseña del usuario"""
        if self.user:
            password = self.cleaned_data['new_password1']
            self.user.set_password(password)
            self.user.clear_password_reset_code()
            self.user.save()
            return self.user
        return None

class ExpertRegisterForm(UserCreationForm):
    email = forms.EmailField(
        label='Correo electrónico profesional',
        required=True,
        help_text='Usa tu email profesional o institucional'
    )
    first_name = forms.CharField(label='Nombres', required=True)
    last_name = forms.CharField(label='Apellidos', required=True)
    
    professional_title = forms.CharField(
        label='Título profesional',
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Ej: Biólogo, Ingeniero Forestal, etc.'})
    )
    
    institution = forms.CharField(
        label='Institución',
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Universidad, Centro de Investigación, etc.'})
    )
    
    years_experience = forms.IntegerField(
        label='Años de experiencia',
        required=True,
        min_value=1,
        max_value=50,
        widget=forms.NumberInput(attrs={'placeholder': '5'})
    )
    
    expertise_areas = forms.CharField(
        label='Áreas de especialización',
        required=True,
        widget=forms.Textarea(attrs={
            'placeholder': 'Ej: Botánica, Ecología, Zoología, Educación Ambiental...',
            'rows': 3
        }),
        help_text='Separa las áreas con comas'
    )
    
    bio = forms.CharField(
        label='Biografía profesional',
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Breve descripción de tu experiencia y logros...',
            'rows': 4
        })
    )
    
    certifications = forms.CharField(
        label='Certificaciones relevantes',
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Certificaciones, cursos, diplomas relevantes...',
            'rows': 3
        })
    )
    
    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'password1', 'password2', 'professional_title',
            'institution', 'years_experience', 'expertise_areas'
        )
        labels = {
            'username': 'Nombre de usuario',
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("❌ Ya existe un usuario con este correo electrónico.")
        
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("❌ El formato del correo electrónico no es válido.")
        
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("❌ Este nombre de usuario ya está en uso.")
        return username
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.user_type = 4  # Experto
        user.professional_title = self.cleaned_data['professional_title']
        user.institution = self.cleaned_data['institution']
        user.years_experience = self.cleaned_data['years_experience']
        user.expertise_areas = self.cleaned_data['expertise_areas']
        user.is_active = False  # Requiere verificación manual
        if commit:
            try:
                send_verification_email(user)
            except Exception as e:
                print(f"Error enviando email: {e}")
        return user