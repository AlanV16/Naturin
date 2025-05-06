from django.urls import path
from . import views

urlpatterns = [path('',views.pagina_central, name='pagina_central'),]