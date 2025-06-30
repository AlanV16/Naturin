from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    path('assign_badge/<int:user_id>/<int:badge_id>/', views.assign_badge, name='assign_badge'),
    path('rankings/', views.view_rankings, name='view_rankings'),
]