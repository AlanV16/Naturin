from django.contrib import admin
from .models import Category, PlantType, Location, Species

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(PlantType)
class PlantTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude')
    search_fields = ('name',)

@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    list_display = ('name', 'scientific_name', 'category', 'conservation_status', 'human_danger')
    list_filter = ('category', 'conservation_status', 'human_danger', 'plant_type')
    search_fields = ('name', 'scientific_name')
    filter_horizontal = ('locations',)
    fieldsets = (
        ('Información básica', {
            'fields': ('name', 'scientific_name', 'description', 'image', 'audio')
        }),
        ('Clasificación', {
            'fields': ('category', 'plant_type', 'kingdom', 'phylum', 'class_name', 'order', 'family', 'genus')
        }),
        ('Estado y Peligro', {
            'fields': ('conservation_status', 'human_danger')
        }),
        ('Ubicación', {
            'fields': ('locations',)
        }),
        ('Características', {
            'fields': ('size', 'weight', 'lifespan', 'diet', 'habitat')
        }),
    )