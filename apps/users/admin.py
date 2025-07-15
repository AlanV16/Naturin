from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Course, Enrollment, Subject, Material, Assignment, AssignmentSubmission

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Información adicional', {
            'fields': ('user_type', 'birth_date', 'school', 'grade', 'avatar'),
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff', 'is_superuser')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'due_date', 'created_by', 'status', 'max_points']
    list_filter = ['status', 'due_date', 'course']
    search_fields = ['title', 'description']
    ordering = ['-created_at']

@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'student', 'submitted_at', 'status', 'grade', 'is_late']
    list_filter = ['status', 'is_late', 'submitted_at']
    search_fields = ['assignment__title', 'student__username']
    ordering = ['-submitted_at']
