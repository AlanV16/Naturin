from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin


from .models import MultimediaCard, MultimediaTag
from .forms import MultimediaCardForm
from apps.common.models import Category, Location


class MultimediaCardListView(ListView):
    """Vista para listar todas las fichas multimedia con filtros"""
    model = MultimediaCard
    template_name = 'multimedia/multimedia_list.html'
    context_object_name = 'multimedia_cards'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = MultimediaCard.objects.filter(is_public=True)
        
        # Filtros
        search = self.request.GET.get('search')
        media_type = self.request.GET.get('media_type')
        category = self.request.GET.get('category')
        educational_level = self.request.GET.get('educational_level')
        location = self.request.GET.get('location')
        
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
        
        return queryset.select_related('category', 'author').prefetch_related('locations')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['locations'] = Location.objects.all()
        context['media_types'] = MultimediaCard.MEDIA_TYPE_CHOICES
        context['educational_levels'] = MultimediaCard.EDUCATIONAL_LEVEL_CHOICES
        return context


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
    success_url = reverse_lazy('multimedia:list')
    success_message = "Ficha multimedia creada exitosamente."
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class MultimediaCardUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    """Vista para editar una ficha multimedia"""
    model = MultimediaCard
    form_class = MultimediaCardForm
    template_name = 'multimedia/multimedia_form.html'
    success_url = reverse_lazy('multimedia:list')
    success_message = "Ficha multimedia actualizada exitosamente."
    
    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user or self.request.user.is_staff


class MultimediaCardDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    """Vista para eliminar una ficha multimedia"""
    model = MultimediaCard
    template_name = 'multimedia/multimedia_confirm_delete.html'
    success_url = reverse_lazy('multimedia:list')
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
