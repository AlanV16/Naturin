from django.urls import path
from . import views

urlpatterns = [
    path('', views.pagina_central, name='home'),
    path('especies/', views.species_list, name='species_list'),
    path('especies/<int:species_id>/', views.species_detail, name='species_detail'),
    path('categoria/<str:category_name>/', views.category_detail, name='category'),  
    path('explorar/', views.explorar, name='explorar'),
    path('juegos/', views.juegos, name='juegos'),
]