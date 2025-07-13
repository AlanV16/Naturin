#!/usr/bin/env python3
"""
Script de prueba para verificar funcionalidades de los dashboards y clases
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NatureIn.settings')
django.setup()

from apps.users.models import User, Conversation, ConversationMessage
from apps.educational_games.gamification.models import Classroom, ClassroomStudent, Activities, ActivityType, GameType, Levels, Notification

class DashboardFunctionalityTest(TestCase):
    """Pruebas para verificar funcionalidades de los dashboards"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear usuarios de prueba
        self.student = User.objects.create_user(
            username='test_student',
            email='student@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Student',
            user_type=1
        )
        
        self.teacher = User.objects.create_user(
            username='test_teacher',
            email='teacher@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Teacher',
            user_type=2
        )
        
        # Crear clase de prueba
        self.classroom = Classroom.objects.create(
            name='Clase de Prueba',
            description='Clase para pruebas',
            grade='Primero',
            section='A',
            code='TEST123',
            teacher=self.teacher
        )
        
        # Inscribir estudiante en la clase
        ClassroomStudent.objects.create(
            classroom=self.classroom,
            student=self.student,
            classroom_name=self.classroom.name
        )
        
        # Crear actividad de prueba
        self.activity = Activities.objects.create(
            title='Actividad de Prueba',
            instructions='Instrucciones de prueba',
            classroom=self.classroom,
            activity_type_id=1,
            content_id=1
        )
        
        # Crear conversación de prueba
        self.conversation = Conversation.objects.create(
            name=f'Chat de {self.classroom.name}'
        )
        self.conversation.participants.add(self.student, self.teacher)
        
        # Crear mensaje de prueba
        ConversationMessage.objects.create(
            conversation=self.conversation,
            sender=self.teacher,
            content='Mensaje de prueba del profesor'
        )
        
        # Crear nivel para el estudiante
        self.level = Levels.objects.create(
            user=self.student,
            level=1,
            accumulated_points=100
        )
        
        # Crear notificación de prueba
        Notification.objects.create(
            recipient=self.student,
            title='Notificación de prueba',
            message='Esta es una notificación de prueba',
            notification_type='achievement_unlocked'
        )
        
        self.client = Client()
    
    def test_student_dashboard_access(self):
        """Probar acceso al dashboard del estudiante"""
        self.client.login(username='test_student', password='testpass123')
        response = self.client.get(reverse('users:dashboard_student', kwargs={'user_id': self.student.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'Test Student')
    
    def test_teacher_dashboard_access(self):
        """Probar acceso al dashboard del profesor"""
        self.client.login(username='test_teacher', password='testpass123')
        response = self.client.get(reverse('users:dashboard_teacher', kwargs={'user_id': self.teacher.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'Test Teacher')
    
    def test_join_class_functionality(self):
        """Probar funcionalidad de unirse a clase"""
        # Crear nuevo estudiante
        new_student = User.objects.create_user(
            username='new_student',
            email='newstudent@test.com',
            password='testpass123',
            user_type=1
        )
        
        self.client.login(username='new_student', password='testpass123')
        
        # Probar unirse a clase
        response = self.client.post(reverse('users:join_class'), {
            'class_code': 'TEST123'
        })
        
        # Verificar que se unió correctamente
        self.assertTrue(ClassroomStudent.objects.filter(
            classroom=self.classroom,
            student=new_student
        ).exists())
    
    def test_class_student_view(self):
        """Probar vista de clase para estudiante"""
        self.client.login(username='test_student', password='testpass123')
        response = self.client.get(reverse('users:class_student', kwargs={'class_id': self.classroom.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Clase de Prueba')
    
    def test_class_teacher_view(self):
        """Probar vista de clase para profesor"""
        self.client.login(username='test_teacher', password='testpass123')
        response = self.client.get(reverse('users:class_teacher', kwargs={'class_id': self.classroom.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Clase de Prueba')
    
    def test_chat_functionality(self):
        """Probar funcionalidad del chat"""
        self.client.login(username='test_student', password='testpass123')
        
        # Probar enviar mensaje
        response = self.client.post(reverse('users:class_chat', kwargs={'class_id': self.classroom.id}), {
            'message': 'Mensaje de prueba del estudiante'
        })
        
        # Verificar que el mensaje se creó
        self.assertTrue(ConversationMessage.objects.filter(
            conversation=self.conversation,
            sender=self.student,
            content='Mensaje de prueba del estudiante'
        ).exists())
    
    def test_avatar_upload(self):
        """Probar subida de avatar"""
        self.client.login(username='test_student', password='testpass123')
        
        # Crear archivo de imagen de prueba
        image_content = b'fake-image-content'
        image_file = SimpleUploadedFile(
            'test_avatar.jpg',
            image_content,
            content_type='image/jpeg'
        )
        
        response = self.client.post(reverse('users:update_avatar'), {
            'avatar': image_file
        })
        
        self.assertEqual(response.status_code, 200)
    
    def test_notifications(self):
        """Probar sistema de notificaciones"""
        self.client.login(username='test_student', password='testpass123')
        
        # Probar obtener notificaciones
        response = self.client.get(reverse('users:notifications_list'))
        self.assertEqual(response.status_code, 200)
        
        # Probar marcar notificación como leída
        notification = Notification.objects.first()
        response = self.client.post(reverse('users:mark_notification_read', kwargs={'notification_id': notification.id}))
        self.assertEqual(response.status_code, 200)
    
    def test_messaging_system(self):
        """Probar sistema de mensajería"""
        self.client.login(username='test_student', password='testpass123')
        
        # Probar lista de mensajes
        response = self.client.get(reverse('users:messages_list'))
        self.assertEqual(response.status_code, 200)
        
        # Probar detalle de conversación
        response = self.client.get(reverse('users:conversation_detail', kwargs={'conversation_id': self.conversation.id}))
        self.assertEqual(response.status_code, 200)
    
    def test_create_class_api(self):
        """Probar API de creación de clase"""
        self.client.login(username='test_teacher', password='testpass123')
        
        response = self.client.post(reverse('users:create_class_api'), {
            'class_name': 'Nueva Clase API',
            'description': 'Descripción de prueba',
            'grade': 'Primero',
            'section': 'B'
        })
        
        self.assertEqual(response.status_code, 200)
        # Verificar que la clase se creó
        self.assertTrue(Classroom.objects.filter(name='Nueva Clase API').exists())
    
    def test_join_class_api(self):
        """Probar API de unirse a clase"""
        self.client.login(username='test_student', password='testpass123')
        
        response = self.client.post(reverse('users:join_class_api'), {
            'code': 'TEST123'
        })
        
        self.assertEqual(response.status_code, 200)
    
    def test_generate_class_code(self):
        """Probar generación de código de clase"""
        self.client.login(username='test_teacher', password='testpass123')
        
        response = self.client.get(reverse('users:generate_class_code'))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('code', data)
        self.assertEqual(len(data['code']), 6)  # Código de 6 caracteres
    
    def test_student_achievements(self):
        """Probar logros del estudiante"""
        self.client.login(username='test_student', password='testpass123')
        
        response = self.client.get(reverse('users:student_achievements'))
        self.assertEqual(response.status_code, 200)
    
    def test_teacher_courses(self):
        """Probar cursos del profesor"""
        self.client.login(username='test_teacher', password='testpass123')
        
        response = self.client.get(reverse('users:teacher_courses'))
        self.assertEqual(response.status_code, 200)
    
    def test_ajax_endpoints(self):
        """Probar endpoints AJAX"""
        self.client.login(username='test_student', password='testpass123')
        
        # Probar endpoint de cursos del estudiante
        response = self.client.get(reverse('users:ajax_student_courses'))
        self.assertEqual(response.status_code, 200)
        
        self.client.login(username='test_teacher', password='testpass123')
        
        # Probar endpoint de cursos del profesor
        response = self.client.get(reverse('users:ajax_teacher_courses'))
        self.assertEqual(response.status_code, 200)
    
    def test_profile_functionality(self):
        """Probar funcionalidades de perfil"""
        self.client.login(username='test_student', password='testpass123')
        
        # Probar acceso a perfil
        response = self.client.get(reverse('users:dashboard_student', kwargs={'user_id': self.student.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Student')
    
    def test_course_detail_redirect(self):
        """Probar redirección de detalle de curso"""
        self.client.login(username='test_student', password='testpass123')
        
        response = self.client.get(reverse('users:course_detail', kwargs={'course_id': self.classroom.id}))
        # Debería redirigir a la vista de clase del estudiante
        self.assertEqual(response.status_code, 302)
    
    def test_unauthorized_access(self):
        """Probar acceso no autorizado"""
        # Intentar acceder sin login
        response = self.client.get(reverse('users:dashboard_student', kwargs={'user_id': self.student.id}))
        self.assertEqual(response.status_code, 302)  # Debería redirigir al login
        
        # Intentar acceder a clase sin estar inscrito
        unauthorized_student = User.objects.create_user(
            username='unauthorized',
            email='unauthorized@test.com',
            password='testpass123',
            user_type=1
        )
        self.client.login(username='unauthorized', password='testpass123')
        
        response = self.client.get(reverse('users:class_student', kwargs={'class_id': self.classroom.id}))
        self.assertEqual(response.status_code, 302)  # Debería redirigir
    
    def tearDown(self):
        """Limpiar datos de prueba"""
        # Eliminar archivos de avatar si existen
        for user in User.objects.all():
            if user.avatar:
                try:
                    user.avatar.delete()
                except:
                    pass
        
        # Limpiar todos los datos de prueba
        User.objects.all().delete()
        Classroom.objects.all().delete()
        Conversation.objects.all().delete()
        Notification.objects.all().delete()

def run_functionality_tests():
    """Ejecutar todas las pruebas de funcionalidad"""
    print("🧪 Iniciando pruebas de funcionalidad...")
    
    # Crear instancia de prueba
    test_instance = DashboardFunctionalityTest()
    test_instance.setUp()
    
    tests = [
        ('Dashboard del Estudiante', test_instance.test_student_dashboard_access),
        ('Dashboard del Profesor', test_instance.test_teacher_dashboard_access),
        ('Unirse a Clase', test_instance.test_join_class_functionality),
        ('Vista de Clase - Estudiante', test_instance.test_class_student_view),
        ('Vista de Clase - Profesor', test_instance.test_class_teacher_view),
        ('Funcionalidad de Chat', test_instance.test_chat_functionality),
        ('Subida de Avatar', test_instance.test_avatar_upload),
        ('Sistema de Notificaciones', test_instance.test_notifications),
        ('Sistema de Mensajería', test_instance.test_messaging_system),
        ('API Crear Clase', test_instance.test_create_class_api),
        ('API Unirse a Clase', test_instance.test_join_class_api),
        ('Generar Código de Clase', test_instance.test_generate_class_code),
        ('Logros del Estudiante', test_instance.test_student_achievements),
        ('Cursos del Profesor', test_instance.test_teacher_courses),
        ('Endpoints AJAX', test_instance.test_ajax_endpoints),
        ('Funcionalidades de Perfil', test_instance.test_profile_functionality),
        ('Redirección de Curso', test_instance.test_course_detail_redirect),
        ('Acceso No Autorizado', test_instance.test_unauthorized_access),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"  🔍 Probando: {test_name}")
            test_func()
            print(f"  ✅ {test_name}: PASÓ")
            passed += 1
        except Exception as e:
            print(f"  ❌ {test_name}: FALLÓ - {str(e)}")
            failed += 1
    
    test_instance.tearDown()
    
    print(f"\n📊 Resumen de Pruebas:")
    print(f"  ✅ Pasadas: {passed}")
    print(f"  ❌ Fallidas: {failed}")
    print(f"  📈 Total: {passed + failed}")
    
    if failed == 0:
        print("🎉 ¡Todas las funcionalidades están trabajando correctamente!")
    else:
        print("⚠️  Algunas funcionalidades necesitan atención.")
    
    return passed, failed

if __name__ == '__main__':
    run_functionality_tests() 