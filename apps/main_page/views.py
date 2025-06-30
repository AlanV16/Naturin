from django.shortcuts import render, get_object_or_404
from django.db import models
from itertools import chain
from apps.plants.models import Plant, PlantType
from apps.animals.models import Animal
from apps.common.models import Category, Location

def main_page(request):
    """Vista para la página principal"""
    plant_qs = Plant.objects.all()
    animals_qs = Animal.objects.all()
    species_count = plant_qs.count() + animals_qs.count()
    categories = Category.objects.all()

    featured_plants = Plant.objects.order_by('?')[:3]
    featured_animals = Animal.objects.order_by('?')[:3]
    featured_species = list(featured_plants) + list(featured_animals)

    places = [
        {
            "slug": "parque-nacional-tingo-maria",
            "name": "Parque Nacional Tingo María",
            "image": ["images/explore/bella_durmiente.png",
                      ]
        },
        {
            "slug": "jardin-botanico",
            "name": "Jardín Botánico",
            "image": [
                "images/explore/orquideas.png",
            ],
        },
        {
            "slug": "cascada-el-leon",
            "name": "Cascada El León",
            "image": [
                "images/explore/catarata_leon.png",
            ],
        },
        {
            "slug": "laguna-de-los-milagros",
            "name": "Laguna de los Milagros",
            "image": [
                "images/explore/laguna_milagros.png",
            ],
        },
        {
            "slug": "cueva-de-las-lechuzas",
            "name": "Cueva de las Lechuzas",
            "image": [
                "images/explore/cueva_lechuzas.png",
            ],
        },
        {
            "slug": "rio-huallaga",
            "name": "Rio Huallaga",
            "image": [
                "images/explore/huallaga.png",
            ],
        },
    ]

    context = {
        'plant_qs': Plant.objects.all(),
        'animals_qs': Animal.objects.all(),
        'species_count': plant_qs.count() + animals_qs.count(),
        'categories': categories,
        'featured_species': featured_species,
        'places': places,
    }

    return render(request, 'main_page/home.html', context)


def category_detail(request, category_name):
    category = get_object_or_404(Category, name__iexact=category_name)
    species = Species.objects.filter(category=category)
    context = {
        'category': category,
        'species': species,
    }
    return render(request, 'apps/main_page/templates/category_detail.html', context)


def species_list(request):
    """Vista para listar todas las especies con filtros"""
    categories = Category.objects.all()
    plant_types = PlantType.objects.all()
    locations = Location.objects.all()

    # Consulta base
    animals_qs = Animal.objects.all()
    plants_qs = Plant.objects.all()

    # Filtrar por categoría
    category_filter = request.GET.get('category')
    if category_filter:
        animals_qs = animals_qs.filter(category__name__iexact=category_filter)
        plants_qs = plants_qs.filter(category__name__iexact=category_filter)

    # Filtrar por tipo de planta (solo aplica a plantas)
    plant_type_filter = request.GET.get('plant_type')
    if plant_type_filter:
        plants_qs = plants_qs.filter(plant_type__name__iexact=plant_type_filter)

    # Filtrar por estado de conservación (ambos modelos deben tener este campo)
    conservation_filter = request.GET.get('conservation')
    if conservation_filter:
        animals_qs = animals_qs.filter(conservation_status=conservation_filter)
        plants_qs = plants_qs.filter(conservation_status=conservation_filter)

    # Filtrar por ubicación (si ambos modelos tienen locations)
    location_filter = request.GET.get('location')
    if location_filter:
        animals_qs = animals_qs.filter(locations__name__iexact=location_filter)
        plants_qs = plants_qs.filter(locations__name__iexact=location_filter)

    # Búsqueda general
    search_query = request.GET.get('search')
    if search_query:
        animals_qs = animals_qs.filter(
            models.Q(name__icontains=search_query) |
            models.Q(scientific_name__icontains=search_query) |
            models.Q(description__icontains=search_query)
        )
        plants_qs = plants_qs.filter(
            models.Q(name__icontains=search_query) |
            models.Q(scientific_name__icontains=search_query) |
            models.Q(description__icontains=search_query)
        )

    # Unir ambos querysets
    species_list = list(chain(animals_qs, plants_qs))

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

    return render(request, 'main_page/species_list.html', context)


def species_detail(request, kind, pk):
    """
    Muestra detalles de una especie concreta.
    kind: 'plant' o 'animal'
    pk:  id de la instancia
    """
    if kind == 'plant':
        obj = get_object_or_404(Plant, pk=pk)
    elif kind == 'animal':
        obj = get_object_or_404(Animal, pk=pk)
    else:
        # si recibes algo distinto, retornas 404
        from django.http import Http404
        raise Http404("Tipo desconocido")

    # especies relacionadas (pueden ser de ambas apps si quieres)
    related_plants  = Plant.objects.filter(category=obj.category).exclude(pk=pk)
    related_animals = Animal.objects.filter(category=obj.category).exclude(pk=pk)
    related = list(related_plants[:3]) + list(related_animals[:3])

    context = {
        'species': obj,
        'related_species': related,
    }
    return render(request, 'apps/main_page/templates/species_detail.html', context)


def explore(request):
    return render(request, 'main_page/explore.html')


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


def games(request):
    """Vista para la sección de juegos"""
    return render(request, 'main_page/games.html')

