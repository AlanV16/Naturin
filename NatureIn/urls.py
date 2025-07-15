from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler404

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('apps.main_page.urls', 'main_page'), namespace='main_page')),
    path('accounts/', include('apps.users.urls')), 
    path('common/', include('apps.common.urls')), 
    path('multimedia/', include('apps.multimedia.urls')),
    path('guias/', include('apps.pedagogical_guides.urls')),
    path('gamification/', include(('apps.educational_games.gamification.urls', 'gamification'), namespace='gamification')),
    path('activities/', include('apps.educational_games.urls')),
    path('content/', include('apps.content.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'NatureIn.views.custom_404_view'