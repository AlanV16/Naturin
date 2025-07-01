from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.main_page.urls')),
    path('accounts/', include('apps.users.urls')), 
    path('common/', include('apps.common.urls')), 
    path('multimedia/', include('apps.multimedia.urls')),
    path('guias/', include('apps.pedagogical_guides.urls')),
    path('gamification/', include('apps.gamification.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)