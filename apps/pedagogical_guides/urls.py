from django.urls import path
from . import views

app_name = 'pedagogical_guides'

urlpatterns = [
    path('', views.guide_list, name='guide_list'),
    path('upload/', views.guide_upload, name='guide_upload'),
    path('download/<int:pk>/', views.guide_download, name='guide_download'),
] 