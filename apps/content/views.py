from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json

from .models import ContentCategory, EducationalSheet

def bella_durmiente_detail(request):
    return render(request, 'content/explore_bella_durmiente.html')

def cueva_lechuzas_detail(request):
    return render(request, 'content/explore_cueva_lechuzas.html')

def laguna_milagros_detail(request):
    return render(request, 'content/explore_laguna_milagros.html')

def jardin_botanico_detail(request):
    return render(request, 'content/explore_jardin_botanico.html')

def cascada_leon_detail(request):
    return render(request, 'content/explore_cascada_leon.html')

def cueva_pavas_detail(request):
    return render(request, 'content/explore_cueva_pavas.html')

def catarata_santa_carmen_detail(request):
    return render(request, 'content/explore_catarata_santa_carmen.html')

def catarata_san_miguel_detail(request):
    return render(request, 'content/explore_catarata_san_miguel.html')

def zoocriadero_detail(request):
    return render(request, 'content/explore_zoocriadero.html')

def rio_huallaga_detail(request):
    return render(request, 'content/explore_rio_huallaga.html')

@login_required
@require_http_methods(["GET"])
def get_categories(request):
    """API para obtener categorías de contenido"""
    categories = ContentCategory.objects.filter(is_active=True).order_by('name')
    
    categories_data = []
    for category in categories:
        categories_data.append({
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'icon': category.icon
        })
    
    return JsonResponse({
        'success': True,
        'categories': categories_data
    })

@login_required
@require_http_methods(["POST"])
def create_sheet(request):
    """API para crear nueva ficha educativa"""
    try:
        # Verificar que el usuario sea experto (tipo 4)
        if request.user.user_type != 4:
            return JsonResponse({
                'success': False,
                'error': 'No tienes permisos para crear fichas educativas'
            })
        
        # Obtener datos del formulario
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        sheet_type = request.POST.get('sheet_type', '').strip()
        tags_data = request.POST.get('tags_data', '{}')
        submit_for_review = request.POST.get('submit_for_review') == 'on'
        
        # Validaciones básicas
        if not all([title, description, sheet_type]):
            return JsonResponse({
                'success': False,
                'error': 'Todos los campos requeridos deben estar completos'
            })
        
        # Validar tipo de ficha
        if sheet_type not in ['flora', 'fauna', 'ecosystem']:
            return JsonResponse({
                'success': False,
                'error': 'Tipo de ficha no válido'
            })
        
        # Procesar tags estructurados
        try:
            tags_dict = json.loads(tags_data)
        except json.JSONDecodeError:
            tags_dict = {}
        
        # Validar tags requeridos según el tipo
        required_tags = {
            'flora': ['clasificacion_biologica', 'estado_conservacion', 'habitat_ecosistema'],
            'fauna': ['clasificacion_biologica', 'estado_conservacion', 'habitat_ecosistema'],
            'ecosystem': ['tipo_ecosistema', 'estado_conservacion']
        }
        
        missing_tags = []
        for tag in required_tags.get(sheet_type, []):
            if tag not in tags_dict or not tags_dict[tag]:
                missing_tags.append(tag.replace('_', ' ').title())
        
        if missing_tags:
            return JsonResponse({
                'success': False,
                'error': f'Faltan tags requeridos: {", ".join(missing_tags)}'
            })
        
        # Determinar el estado inicial
        if submit_for_review:
            status = 'pending_review'
            message = 'Ficha creada y enviada para revisión exitosamente'
        else:
            status = 'draft'
            message = 'Borrador de ficha guardado exitosamente'
        
        # Crear categoría automáticamente basada en el tipo
        category_name = {
            'flora': 'Flora y Vegetación',
            'fauna': 'Fauna y Vida Animal',
            'ecosystem': 'Ecosistemas y Lugares'
        }[sheet_type]
        
        # Obtener o crear la categoría
        category, created = ContentCategory.objects.get_or_create(
            name=category_name,
            defaults={
                'description': f'Fichas educativas de {category_name.lower()}',
                'is_active': True
            }
        )
        
        # Crear la ficha
        sheet = EducationalSheet.objects.create(
            title=title,
            description=description,
            content=f"Tipo: {sheet_type.title()}\n\nEtiquetas:\n{json.dumps(tags_dict, indent=2, ensure_ascii=False)}",
            category=category,
            tags=json.dumps(tags_dict, ensure_ascii=False),
            difficulty='intermediate',  # Valor por defecto
            status=status,
            author=request.user,
            sheet_type=sheet_type  # Necesitaremos agregar este campo al modelo
        )
        
        # Procesar archivos si existen
        if 'featured_image' in request.FILES:
            sheet.featured_image = request.FILES['featured_image']
        
        if 'attachments' in request.FILES:
            sheet.attachments = request.FILES['attachments']
        
        sheet.save()
        
        return JsonResponse({
            'success': True,
            'message': message,
            'sheet_id': sheet.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        })

@login_required
@require_http_methods(["GET"])
def get_expert_sheets(request):
    """API para obtener fichas del experto actual"""
    if request.user.user_type != 4:
        return JsonResponse({
            'success': False,
            'error': 'No tienes permisos para ver estas fichas'
        })
    
    sheets = EducationalSheet.objects.filter(
        author=request.user
    ).select_related('category').order_by('-created_at')
    
    sheets_data = []
    for sheet in sheets:
        # Procesar tags si están en formato JSON
        try:
            tags_dict = json.loads(sheet.tags) if sheet.tags else {}
        except (json.JSONDecodeError, TypeError):
            tags_dict = {}
        
        sheets_data.append({
            'id': sheet.id,
            'title': sheet.title,
            'description': sheet.description,
            'sheet_type': sheet.sheet_type,
            'category_name': sheet.category.name,
            'status': sheet.status,
            'status_display': sheet.get_status_display(),
            'created_at': sheet.created_at.isoformat(),
            'updated_at': sheet.updated_at.isoformat(),
            'image': sheet.featured_image.url if sheet.featured_image else None,
            'tags': tags_dict,
            'views_count': sheet.views_count,
            'downloads_count': sheet.downloads_count
        })
    
    return JsonResponse({
        'success': True,
        'sheets': sheets_data
    })
