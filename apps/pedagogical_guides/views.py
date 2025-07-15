from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from .models import Guide, GuideCategory, GuideTag, GuideRating
from .forms import GuideForm
from apps.common.models import Category, Location

@login_required
def guide_list(request):
    """Lista de guías pedagógicas con filtros"""
    guides = Guide.objects.filter(is_public=True)
    
    # Filtros
    category_id = request.GET.get('category')
    content_type = request.GET.get('content_type')
    educational_level = request.GET.get('educational_level')
    search = request.GET.get('search')
    
    if category_id:
        guides = guides.filter(category_id=category_id)
    if content_type:
        guides = guides.filter(content_type=content_type)
    if educational_level:
        guides = guides.filter(educational_level=educational_level)
    if search:
        guides = guides.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(subject_area__icontains=search)
        )
    
    # Ordenamiento
    sort_by = request.GET.get('sort', '-created_at')
    guides = guides.order_by(sort_by)
    
    # Paginación
    paginator = Paginator(guides, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': GuideCategory.objects.all(),
        'content_types': Guide.CONTENT_TYPE_CHOICES,
        'educational_levels': Guide.EDUCATIONAL_LEVEL_CHOICES,
        'filters': {
            'category_id': category_id,
            'content_type': content_type,
            'educational_level': educational_level,
            'search': search,
            'sort': sort_by,
        }
    }
    
    return render(request, 'pedagogical_guides/guide_list.html', context)

@login_required
def guide_detail(request, guide_id):
    """Detalle de una guía pedagógica"""
    guide = get_object_or_404(Guide, id=guide_id, is_public=True)
    
    # Incrementar vistas
    guide.increment_views()
    
    # Obtener calificaciones recientes
    recent_ratings = guide.ratings.all().order_by('-created_at')[:5]
    
    # Verificar si el usuario ya calificó
    user_rating = None
    if request.user.is_authenticated:
        user_rating = GuideRating.objects.filter(guide=guide, user=request.user).first()
    
    context = {
        'guide': guide,
        'recent_ratings': recent_ratings,
        'user_rating': user_rating,
    }
    
    return render(request, 'pedagogical_guides/guide_detail.html', context)

@login_required
def guide_upload(request):
    """Subir nueva guía pedagógica"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden subir guías pedagógicas.')
        return redirect('pedagogical_guides:guide_list')
    
    if request.method == 'POST':
        form = GuideForm(request.POST, request.FILES)
        if form.is_valid():
            guide = form.save(commit=False)
            guide.author = request.user
            guide.save()
            form.save_m2m()  # Guardar relaciones many-to-many
            
            messages.success(request, 'Guía pedagógica subida exitosamente.')
            return redirect('pedagogical_guides:guide_detail', guide_id=guide.id)
        else:
            messages.error(request, 'Error al subir la guía. Por favor, revisa los datos.')
    else:
        form = GuideForm()
    
    context = {
        'form': form,
        'categories': GuideCategory.objects.all(),
        'locations': Location.objects.all(),
    }
    
    return render(request, 'pedagogical_guides/guide_upload.html', context)

@login_required
def guide_edit(request, guide_id):
    """Editar guía pedagógica"""
    guide = get_object_or_404(Guide, id=guide_id, author=request.user)
    
    if request.method == 'POST':
        form = GuideForm(request.POST, request.FILES, instance=guide)
        if form.is_valid():
            form.save()
            messages.success(request, 'Guía pedagógica actualizada exitosamente.')
            return redirect('pedagogical_guides:guide_detail', guide_id=guide.id)
        else:
            messages.error(request, 'Error al actualizar la guía.')
    else:
        form = GuideForm(instance=guide)
    
    context = {
        'form': form,
        'guide': guide,
        'categories': GuideCategory.objects.all(),
        'locations': Location.objects.all(),
    }
    
    return render(request, 'pedagogical_guides/guide_edit.html', context)

@login_required
def guide_delete(request, guide_id):
    """Eliminar guía pedagógica"""
    guide = get_object_or_404(Guide, id=guide_id, author=request.user)
    
    if request.method == 'POST':
        guide.delete()
        messages.success(request, 'Guía pedagógica eliminada exitosamente.')
        return redirect('pedagogical_guides:guide_list')
    
    return render(request, 'pedagogical_guides/guide_confirm_delete.html', {'guide': guide})

@login_required
def guide_rate(request, guide_id):
    """Calificar guía pedagógica"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    guide = get_object_or_404(Guide, id=guide_id, is_public=True)
    rating_value = request.POST.get('rating')
    comment = request.POST.get('comment', '')
    
    if not rating_value:
        return JsonResponse({'success': False, 'error': 'Calificación requerida'})
    
    try:
        rating_value = int(rating_value)
        if rating_value < 1 or rating_value > 5:
            return JsonResponse({'success': False, 'error': 'Calificación inválida'})
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Calificación inválida'})
    
    # Crear o actualizar calificación
    rating, created = GuideRating.objects.get_or_create(
        guide=guide,
        user=request.user,
        defaults={'rating': rating_value, 'comment': comment}
    )
    
    if not created:
        rating.rating = rating_value
        rating.comment = comment
        rating.save()
    
    # Actualizar calificación promedio de la guía
    guide.update_rating(rating_value)
    
    return JsonResponse({
        'success': True,
        'message': 'Calificación guardada exitosamente',
        'new_rating': float(guide.rating),
        'rating_count': guide.rating_count
    })

@login_required
def guide_download(request, guide_id):
    """Descargar guía pedagógica"""
    guide = get_object_or_404(Guide, id=guide_id, is_public=True)
    
    # Incrementar contador de descargas
    guide.increment_downloads()
    
    # Obtener archivo para descarga
    file_to_download = guide.get_media_file()
    
    if not file_to_download:
        messages.error(request, 'No hay archivo disponible para descargar.')
        return redirect('pedagogical_guides:guide_detail', guide_id=guide.id)
    
    # Aquí implementarías la lógica de descarga del archivo
    # Por ahora solo redirigimos
    messages.success(request, 'Descarga iniciada.')
    return redirect('pedagogical_guides:guide_detail', guide_id=guide.id)

@login_required
def my_guides(request):
    """Guías del usuario actual"""
    if request.user.user_type != 2:  # Solo docentes
        messages.error(request, 'Solo los docentes pueden acceder a esta página.')
        return redirect('pedagogical_guides:guide_list')
    
    guides = Guide.objects.filter(author=request.user).order_by('-created_at')
    
    # Estadísticas
    total_guides = guides.count()
    total_views = guides.aggregate(Sum('views_count'))['views_count__sum'] or 0
    total_downloads = guides.aggregate(Sum('downloads_count'))['downloads_count__sum'] or 0
    avg_rating = guides.aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'guides': guides,
        'total_guides': total_guides,
        'total_views': total_views,
        'total_downloads': total_downloads,
        'avg_rating': avg_rating,
    }
    
    return render(request, 'pedagogical_guides/my_guides.html', context)

@login_required
def guide_categories(request):
    """Lista de categorías de guías"""
    categories = GuideCategory.objects.annotate(
        guide_count=Count('guides')
    ).order_by('name')
    
    return render(request, 'pedagogical_guides/categories.html', {'categories': categories})

@login_required
def category_guides(request, category_id):
    """Guías por categoría"""
    category = get_object_or_404(GuideCategory, id=category_id)
    guides = Guide.objects.filter(category=category, is_public=True).order_by('-created_at')
    
    # Paginación
    paginator = Paginator(guides, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    
    return render(request, 'pedagogical_guides/category_guides.html', context)

# APIs para funcionalidades AJAX
@login_required
def guide_search_api(request):
    """API para búsqueda de guías"""
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse({'guides': []})
    
    guides = Guide.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(subject_area__icontains=query),
        is_public=True
    )[:10]
    
    results = []
    for guide in guides:
        results.append({
            'id': guide.id,
            'title': guide.title,
            'description': guide.description[:100] + '...' if len(guide.description) > 100 else guide.description,
            'content_type': guide.get_content_type_display_name(),
            'category': guide.category.name,
            'rating': float(guide.rating),
            'views_count': guide.views_count,
        })
    
    return JsonResponse({'guides': results})

@login_required
def guide_stats_api(request, guide_id):
    """API para estadísticas de guía"""
    guide = get_object_or_404(Guide, id=guide_id)
    
    return JsonResponse({
        'views_count': guide.views_count,
        'downloads_count': guide.downloads_count,
        'rating': float(guide.rating),
        'rating_count': guide.rating_count,
    })

def guide_download(request, pk):
    guide = get_object_or_404(Guide, pk=pk, is_public=True)
    filename = guide.pdf.name.split('/')[-1]
    response = HttpResponse(guide.pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
