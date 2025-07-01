from django import forms
from .models import Guide

class GuideForm(forms.ModelForm):
    class Meta:
        model = Guide
        fields = ['title', 'description', 'pdf', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título de la guía'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descripción de la guía'}),
            'pdf': forms.FileInput(attrs={'class': 'form-control', 'accept': 'application/pdf'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_pdf(self):
        pdf = self.cleaned_data.get('pdf')
        if pdf and not pdf.name.endswith('.pdf'):
            raise forms.ValidationError('Solo se permiten archivos PDF.')
        return pdf 