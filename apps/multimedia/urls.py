from django.urls import path
from . import views

app_name = 'multimedia'

urlpatterns = [
    # Vistas principales
    path('', views.MultimediaCardListView.as_view(), name='list'),
    path('search/', views.multimedia_search, name='search'),
    path('dashboard/', views.multimedia_dashboard, name='dashboard'),
    
    # CRUD de fichas multimedia
    path('create/', views.MultimediaCardCreateView.as_view(), name='create'),
    path('<int:pk>/', views.MultimediaCardDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.MultimediaCardUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.MultimediaCardDeleteView.as_view(), name='delete'),
    
    # Acciones adicionales
    path('<int:pk>/download/', views.multimedia_download, name='download'),
    path('<int:pk>/toggle-featured/', views.multimedia_toggle_featured, name='toggle_featured'),
    
    # Vistas por categoría
    path('category/<int:category_id>/', views.multimedia_by_category, name='by_category'),
] 