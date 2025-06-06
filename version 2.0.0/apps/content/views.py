from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from .models import Especie, Categoria

class HomeView(TemplateView):
    template_name = "home.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

def species_list(request):
    categorias = Categoria.objects.all()
    especies = Especie.objects.all()
    return render(request, 'content/species_list.html', {
        'categorias': categorias,
        'especies': especies
    })

def species_detail(request, especie_id):
    especie = get_object_or_404(Especie, id=especie_id)
    # Ajusta las relaciones según tu modelo
    return render(request, 'content/species_detail.html', {
        'especie': especie,
        # Agrega aquí relaciones si existen, por ejemplo:
        # 'imagenes': especie.imagenes.all(),
        # 'sonidos': especie.sonidos.all(),
        # 'recursos': especie.recursos_educativos.all(),
    })