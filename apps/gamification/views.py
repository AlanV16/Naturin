from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification

# Sistema de notificaciones
@login_required
def notifications_list(request):
    """Vista para mostrar todas las notificaciones del usuario"""
    notifications = request.user.notifications.all()
    return render(request, 'gamification/notifications_list.html', {'notifications': notifications})

@login_required
def notifications_ajax(request):
    """Vista AJAX para obtener las notificaciones recientes en formato JSON"""
    notifications = request.user.notifications.all()
    notifications_data = []
    
    for notification in notifications:
        notifications_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'is_read': notification.is_read,
            'created_at': notification.created_at.strftime('%d/%m/%Y %H:%M'),
            'notification_type': notification.get_notification_type_display()
        })
    
    return JsonResponse({'notifications': notifications_data})

@login_required
def notifications_count(request):
    """Vista AJAX para obtener el conteo de notificaciones no leídas"""
    unread_count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'unread_count': unread_count})

@login_required
def mark_notification_read(request, notification_id):
    """Vista AJAX para marcar una notificación como leída"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})

@login_required
def mark_all_notifications_read(request):
    """Vista AJAX para marcar todas las notificaciones como leídas"""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return JsonResponse({'success': True})

def create_notification(recipient, notification_type, title, message):
    """Función helper para crear notificaciones"""
    return Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message
    )
