from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    # URLs de Notificaciones
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/ajax/', views.notifications_ajax, name='notifications_ajax'),
    path('notifications/count/', views.notifications_count, name='notifications_count'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
] 