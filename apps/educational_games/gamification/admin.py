from django.contrib import admin
from .models import (
    Classroom, ClassroomStudent, Activities, Niveles
)

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'teacher', 'grade', 'section', 'institution_id')
    list_filter = ('grade', 'section', 'institution_id')
    search_fields = ('name', 'code', 'teacher__username')
    readonly_fields = ('code',)

@admin.register(ClassroomStudent)
class ClassroomStudentAdmin(admin.ModelAdmin):
    list_display = ('classroom', 'student', 'classroom_name')
    list_filter = ('classroom',)
    search_fields = ('classroom__name', 'student__username')

@admin.register(Activities)
class ActivitiesAdmin(admin.ModelAdmin):
    list_display = ('Titulo', 'IDtipoActividad', 'IDaula', 'IDficha')
    list_filter = ('IDtipoActividad',)
    search_fields = ('Titulo', 'IDaula__name')

@admin.register(Niveles)
class NivelesAdmin(admin.ModelAdmin):
    list_display = ('IDusuario', 'nivel', 'puntos_acumulados', 'fecha_actualizacion')
    list_filter = ('nivel',)
    search_fields = ('IDusuario__username',) 