from django.urls import path
from . import views

urlpatterns = [
    path('explore/bella-durmiente/', views.bella_durmiente_detail, name='explore_bella_durmiente'),
    path('explore/cueva-lechuzas/', views.cueva_lechuzas_detail, name='explore_cueva_lechuzas'),
    path('explore/laguna-milagros/', views.laguna_milagros_detail, name='explore_laguna_milagros'),
    path('explore/jardin-botanico/', views.jardin_botanico_detail, name='explore_jardin_botanico'),
    path('explore/cascada-leon/', views.cascada_leon_detail, name='explore_cascada_leon'),
    path('explore/cueva-pavas/', views.cueva_pavas_detail, name='explore_cueva_pavas'),
    path('explore/catarata-santa-carmen/', views.catarata_santa_carmen_detail, name='explore_catarata_santa_carmen'),
    path('explore/catarata-san-miguel/', views.catarata_san_miguel_detail, name='explore_catarata_san_miguel'),
    path('explore/zoocriadero/', views.zoocriadero_detail, name='explore_zoocriadero'),
    path('explore/rio-huallaga/', views.rio_huallaga_detail, name='explore_rio_huallaga'),
] 