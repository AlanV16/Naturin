from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='home'),
    path('especies/', views.species_list, name='species_list'),
    path('especies/<int:species_id>/', views.species_detail, name='species_detail'),
    path('categoria/<str:category_name>/', views.category_detail, name='category'),
    path('explore/', views.explore, name='explore'),
    path('explore/<slug:slug>/', views.explore_detail, name='explore_detail'),
    path('juegos/', views.games, name='games'),
]
