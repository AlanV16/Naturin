from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin


from .models import MultimediaCard, MultimediaTag
from .forms import MultimediaCardForm
from apps.common.models import Category, Location


class MultimediaCardDetailView(DetailView):
    """Vista para mostrar los detalles de una ficha multimedia"""
    model = MultimediaCard
    template_name = 'multimedia/multimedia_detail.html'
    context_object_name = 'multimedia_card'
    
    def get_object(self):
        obj = super().get_object()
        # Incrementar contador de vistas
        obj.increment_views()
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener fichas relacionadas
        context['related_cards'] = MultimediaCard.objects.filter(
            category=self.object.category,
            is_public=True
        ).exclude(id=self.object.id)[:6]
        return context


class MultimediaCardCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Vista para crear una nueva ficha multimedia"""
    model = MultimediaCard
    form_class = MultimediaCardForm
    template_name = 'multimedia/multimedia_form.html'
    success_url = reverse_lazy('multimedia:multimedia_tab')
    success_message = "Ficha multimedia creada exitosamente."
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class MultimediaCardUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    """Vista para editar una ficha multimedia"""
    model = MultimediaCard
    form_class = MultimediaCardForm
    template_name = 'multimedia/multimedia_form.html'
    success_url = reverse_lazy('multimedia:multimedia_tab')
    success_message = "Ficha multimedia actualizada exitosamente."
    
    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user or self.request.user.is_staff


class MultimediaCardDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    """Vista para eliminar una ficha multimedia"""
    model = MultimediaCard
    template_name = 'multimedia/multimedia_confirm_delete.html'
    success_url = reverse_lazy('multimedia:multimedia_tab')
    success_message = "Ficha multimedia eliminada exitosamente."
    
    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user or self.request.user.is_staff


@login_required
def multimedia_dashboard(request):
    """Dashboard para gestionar fichas multimedia del usuario"""
    user_cards = MultimediaCard.objects.filter(author=request.user).order_by('-created_at')
    
    context = {
        'user_cards': user_cards,
        'total_cards': user_cards.count(),
        'public_cards': user_cards.filter(is_public=True).count(),
        'featured_cards': user_cards.filter(is_featured=True).count(),
    }
    
    return render(request, 'multimedia/multimedia_dashboard.html', context)


@login_required
def multimedia_download(request, pk):
    """Vista para descargar una ficha multimedia"""
    multimedia_card = get_object_or_404(MultimediaCard, pk=pk, is_public=True)
    
    # Incrementar contador de descargas
    multimedia_card.increment_downloads()
    
    # Obtener el archivo principal
    media_file = multimedia_card.get_media_file()
    
    if media_file and media_file.storage.exists(media_file.name):
        response = HttpResponse(media_file, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{media_file.name}"'
        return response
    else:
        messages.error(request, "El archivo no está disponible para descarga.")
        return redirect('multimedia:detail', pk=pk)


@require_POST
@login_required
def multimedia_toggle_featured(request, pk):
    """Vista para marcar/desmarcar como destacada una ficha multimedia"""
    multimedia_card = get_object_or_404(MultimediaCard, pk=pk)
    
    # Solo el autor o staff puede marcar como destacada
    if multimedia_card.author == request.user or request.user.is_staff:
        multimedia_card.is_featured = not multimedia_card.is_featured
        multimedia_card.save()
        
        status = "destacada" if multimedia_card.is_featured else "no destacada"
        messages.success(request, f"Ficha marcada como {status}.")
    else:
        messages.error(request, "No tienes permisos para realizar esta acción.")
    
    return redirect('multimedia:detail', pk=pk)


def multimedia_by_category(request, category_id):
    """Vista para mostrar fichas multimedia por categoría"""
    category = get_object_or_404(Category, id=category_id)
    multimedia_cards = MultimediaCard.objects.filter(
        category=category,
        is_public=True
    ).select_related('author').prefetch_related('locations')
    
    paginator = Paginator(multimedia_cards, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'multimedia_cards': page_obj,
    }
    
    return render(request, 'multimedia/multimedia_by_category.html', context)


def multimedia_search(request):
    """Vista para búsqueda avanzada de fichas multimedia"""
    query = request.GET.get('q', '')
    multimedia_cards = []
    
    if query:
        multimedia_cards = MultimediaCard.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(subject_area__icontains=query) |
            Q(learning_objectives__icontains=query),
            is_public=True
        ).select_related('category', 'author').prefetch_related('locations')
    
    context = {
        'query': query,
        'multimedia_cards': multimedia_cards,
        'results_count': multimedia_cards.count(),
    }
    
    return render(request, 'multimedia/multimedia_search.html', context)


def multimedia_tab(request):
    queryset = MultimediaCard.objects.filter(is_public=True)
    search = request.GET.get('search')
    media_type = request.GET.get('media_type')
    category = request.GET.get('category')
    educational_level = request.GET.get('educational_level')
    location = request.GET.get('location')
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(subject_area__icontains=search)
        )
    if media_type:
        queryset = queryset.filter(media_type=media_type)
    if category:
        queryset = queryset.filter(category__name__iexact=category)
    if educational_level:
        queryset = queryset.filter(educational_level=educational_level)
    if location:
        queryset = queryset.filter(locations__name__iexact=location)
    queryset = queryset.select_related('category', 'author').prefetch_related('locations')
    paginator = Paginator(queryset, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    user_cards = None
    if request.user.is_authenticated:
        user_cards = MultimediaCard.objects.filter(author=request.user).order_by('-created_at')
    # Estadísticas
    featured_count = queryset.filter(is_featured=True).count()
    total_views = queryset.aggregate(total_views=Sum('views_count'))['total_views'] or 0
    total_downloads = queryset.aggregate(total_downloads=Sum('downloads_count'))['total_downloads'] or 0
    context = {
        'multimedia_cards': page_obj,
        'categories': Category.objects.all(),
        'locations': Location.objects.all(),
        'media_types': MultimediaCard.MEDIA_TYPE_CHOICES,
        'educational_levels': MultimediaCard.EDUCATIONAL_LEVEL_CHOICES,
        'page_obj': page_obj,
        'request': request,
        'user_cards': user_cards,
        'featured_count': featured_count,
        'total_views': total_views,
        'total_downloads': total_downloads,
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Si es AJAX, solo renderizar el grid
        return render(request, 'multimedia/tabs/multimedia_tab_grid.html', context)
    return render(request, 'multimedia/tabs/multimedia_tab.html', context)


def mapa_tab(request):
    return render(request, 'main_page/tabs/mapa_tab.html')
