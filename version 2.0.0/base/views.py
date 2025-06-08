from django.shortcuts import render, get_object_or_404
from django.db import models
from .models import Species, Category, PlantType, Location

def pagina_central(request):
    """Vista para la página principal"""
    species_count = Species.objects.count()
    categories = Category.objects.all()
    
    featured_species = Species.objects.order_by('?')[:6]
    
    context = {
        'species_count': species_count,
        'categories': categories,
        'featured_species': featured_species,
    }
    
    return render(request, 'base/home.html', context)

def category_detail(request, category_name):
    category = get_object_or_404(Category, name__iexact=category_name)
    species = Species.objects.filter(category=category)
    context = {
        'category': category,
        'species': species,
    }
    return render(request, 'base/category_detail.html', context)

def species_list(request):
    """Vista para listar todas las especies con filtros"""
    categories = Category.objects.all()
    species_list = Species.objects.all()
    plant_types = PlantType.objects.all()
    locations = Location.objects.all()
    
    # Filtrar por categoría
    category_filter = request.GET.get('category')
    if category_filter:
        species_list = species_list.filter(category__name__iexact=category_filter)
    
    # Filtrar por tipo de planta
    plant_type_filter = request.GET.get('plant_type')
    if plant_type_filter:
        species_list = species_list.filter(plant_type__name__iexact=plant_type_filter)
    
    # Filtrar por estado de conservación
    conservation_filter = request.GET.get('conservation')
    if conservation_filter:
        species_list = species_list.filter(conservation_status=conservation_filter)
    
    # Filtrar por ubicación
    location_filter = request.GET.get('location')
    if location_filter:
        species_list = species_list.filter(locations__name__iexact=location_filter)
    
    # Búsqueda general
    search_query = request.GET.get('search')
    if search_query:
        species_list = species_list.filter(
            models.Q(name__icontains=search_query) | 
            models.Q(scientific_name__icontains=search_query) |
            models.Q(description__icontains=search_query)
        )
    
    context = {
        'categories': categories,
        'species_list': species_list,
        'plant_types': plant_types,
        'locations': locations,
        'active_category': category_filter,
        'active_plant_type': plant_type_filter,
        'active_conservation': conservation_filter,
        'active_location': location_filter,
        'search_query': search_query,
    }
    
    return render(request, 'base/species_list.html', context)

def species_detail(request, species_id):
    """Vista para mostrar detalles de una especie específica"""
    species = get_object_or_404(Species, id=species_id)
    
    related_species = Species.objects.filter(
        models.Q(category=species.category) | 
        models.Q(locations__in=species.locations.all())
    ).exclude(id=species.id).distinct()[:3]
    
    context = {
        'species': species,
        'related_species': related_species,
    }
    
    return render(request, 'base/species_detail.html', context)

def explore(request):
    return render(request, 'base/explore.html')

def explore_detail(request, slug):
    # Diccionario de cada slug con su template
    slug_to_template = {
        'parque-nacional-tingo-maria': 'base/explore/explore_tingo_maria.html',
        'jardin-botanico': 'base/explore/explore_jardin_botanico.html',
        'cascada-el-leon': 'base/explore/explore_cascada_leon.html',
        'laguna-de-los-milagros': 'base/explore/explore_laguna_milagros.html',
        'cueva-de-las-lechuzas': 'base/explore/explore_cueva_lechuzas.html',
        'rio-huallaga': 'base/explore/explore_rio_huallaga.html',
        'catarata-santa-carmen': 'base/explore/explore_catarata_santa_carmen.html',
        'zoocriadero-unas': 'base/explore/explore_zoocriadero_unas.html',
        'cueva-de-las-pavas': 'base/explore/explore_cueva_pavas.html',
        'catarata-san-miguel': 'base/explore/explore_catarata_san_miguel.html',
    }
    template = slug_to_template.get(slug)
    if not template:
        # 404 si no existe el slug 
        from django.http import Http404
        raise Http404("Lugar no encontrado")
    return render(request, template, {'slug': slug})

