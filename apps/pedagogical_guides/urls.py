from django.urls import path
from . import views

app_name = 'pedagogical_guides'

urlpatterns = [
    path('', views.guide_list, name='guide_list'),
    path('upload/', views.guide_upload, name='guide_upload'),
    path('my-guides/', views.my_guides, name='my_guides'),
    path('categories/', views.guide_categories, name='guide_categories'),
    path('category/<int:category_id>/', views.category_guides, name='category_guides'),
    path('<int:guide_id>/', views.guide_detail, name='guide_detail'),
    path('<int:guide_id>/edit/', views.guide_edit, name='guide_edit'),
    path('<int:guide_id>/delete/', views.guide_delete, name='guide_delete'),
    path('<int:guide_id>/rate/', views.guide_rate, name='guide_rate'),
    path('<int:guide_id>/download/', views.guide_download, name='guide_download'),
    
    # APIs
    path('api/search/', views.guide_search_api, name='guide_search_api'),
    path('api/<int:guide_id>/stats/', views.guide_stats_api, name='guide_stats_api'),
] 