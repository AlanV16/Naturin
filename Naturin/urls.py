from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.shortcuts import redirect
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('base.urls')),
    path('cuentas/', include('apps.accounts.urls', namespace='accounts')),
    path('dashboard/', lambda request: redirect('home')),  # Redirige a 'home'

    path('contenido/', include('apps.content.urls', namespace='content')),
    path('gamificacion/', include('apps.gamification.urls', namespace='gamification')),
    path('aulas/', include('apps.classrooms.urls', namespace='classrooms')),
    path('interactivo/', include('apps.interactive.urls', namespace='interactive')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)