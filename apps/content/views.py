from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from .models import Species

class HomeView(TemplateView):
    template_name = "home.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

def species_list(request):
    categories = SpeciesCategory.objects.all()
    featured_species = Species.objects.filter(images__is_featured=True).distinct()
    return render(request, 'content/species_list.html', {
        'categories': categories,
        'featured_species': featured_species
    })

def species_detail(request, slug):
    species = get_object_or_404(Species, slug=slug)
    return render(request, 'content/species_detail.html', {
        'species': species,
        'images': species.images.all(),
        'sounds': species.sounds.all(),
        'resources': species.educationalresource_set.all()
    })