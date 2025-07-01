from django import forms
from django.core.exceptions import ValidationError
from .models import MultimediaCard, MultimediaTag
from apps.common.models import Category, Location


class MultimediaCardForm(forms.ModelForm):
    """Formulario para crear y editar fichas multimedia"""
    
    class Meta:
        model = MultimediaCard
        fields = [
            'title', 'description', 'media_type', 'video_file', 'audio_file', 
            'image_file', 'document_file', 'external_url', 'educational_level',
            'subject_area', 'learning_objectives', 'duration', 'category', 
            'locations', 'is_public', 'is_featured'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la ficha multimedia'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción detallada del contenido multimedia'
            }),
            'media_type': forms.Select(attrs={
                'class': 'form-select',
                'id': 'media-type-select'
            }),
            'video_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'video/*'
            }),
            'audio_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'audio/*'
            }),
            'image_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'document_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.ppt,.pptx,.txt'
            }),
            'external_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://ejemplo.com/contenido'
            }),
            'educational_level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'subject_area': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Biología, Ecología, Conservación'
            }),
            'learning_objectives': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Objetivos de aprendizaje que se logran con este contenido'
            }),
            'duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Duración en minutos'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'locations': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 5
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hacer que locations sea opcional
        self.fields['locations'].required = False
        
        # Agregar clases CSS adicionales
        for field_name, field in self.fields.items():
            if hasattr(field, 'widget') and hasattr(field.widget, 'attrs'):
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-control'
        
        # Configurar campos de archivo específicos
        self.fields['video_file'].widget.attrs.update({
            'data-media-type': 'video',
            'style': 'display: none;'
        })
        self.fields['audio_file'].widget.attrs.update({
            'data-media-type': 'audio',
            'style': 'display: none;'
        })
        self.fields['image_file'].widget.attrs.update({
            'data-media-type': 'image',
            'style': 'display: none;'
        })
        self.fields['document_file'].widget.attrs.update({
            'data-media-type': 'document',
            'style': 'display: none;'
        })
        self.fields['external_url'].widget.attrs.update({
            'data-media-type': 'interactive',
            'style': 'display: none;'
        })
    
    def clean(self):
        cleaned_data = super().clean()
        media_type = cleaned_data.get('media_type')
        
        # Validar que se proporcione el archivo correcto según el tipo de medio
        if media_type == 'video':
            if not cleaned_data.get('video_file') and not cleaned_data.get('external_url'):
                raise ValidationError("Para contenido de video, debes proporcionar un archivo de video o una URL externa.")
        
        elif media_type == 'audio':
            if not cleaned_data.get('audio_file') and not cleaned_data.get('external_url'):
                raise ValidationError("Para contenido de audio, debes proporcionar un archivo de audio o una URL externa.")
        
        elif media_type == 'image':
            if not cleaned_data.get('image_file') and not cleaned_data.get('external_url'):
                raise ValidationError("Para contenido de imagen, debes proporcionar una imagen o una URL externa.")
        
        elif media_type == 'document':
            if not cleaned_data.get('document_file') and not cleaned_data.get('external_url'):
                raise ValidationError("Para contenido de documento, debes proporcionar un archivo de documento o una URL externa.")
        
        elif media_type == 'interactive':
            if not cleaned_data.get('external_url'):
                raise ValidationError("Para contenido interactivo, debes proporcionar una URL externa.")
        
        # Validar duración
        duration = cleaned_data.get('duration')
        if duration and duration <= 0:
            raise ValidationError("La duración debe ser mayor a 0 minutos.")
        
        return cleaned_data
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 5:
            raise ValidationError("El título debe tener al menos 5 caracteres.")
        return title
    
    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description) < 20:
            raise ValidationError("La descripción debe tener al menos 20 caracteres.")
        return description


class MultimediaSearchForm(forms.Form):
    """Formulario para búsqueda avanzada de fichas multimedia"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar en títulos, descripciones...'
        })
    )
    
    media_type = forms.ChoiceField(
        choices=[('', 'Todos los tipos')] + MultimediaCard.MEDIA_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="Todas las categorías",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    educational_level = forms.ChoiceField(
        choices=[('', 'Todos los niveles')] + MultimediaCard.EDUCATIONAL_LEVEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    location = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        empty_label="Todas las ubicaciones",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    is_featured = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class MultimediaTagForm(forms.ModelForm):
    """Formulario para crear y editar etiquetas multimedia"""
    
    class Meta:
        model = MultimediaTag
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la etiqueta'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 2:
            raise ValidationError("El nombre de la etiqueta debe tener al menos 2 caracteres.")
        return name 