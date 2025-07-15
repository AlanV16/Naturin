from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from apps.educational_games.models import Assignment
from apps.educational_games.gamification.models import Classroom
from apps.educational_games.models import ClassroomActivity
from django.core.files.uploadedfile import SimpleUploadedFile
import io

User = get_user_model()

class AssignmentCRUDTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(username='profe', password='test123', user_type=2)
        self.client.login(username='profe', password='test123')
        self.classroom = Classroom.objects.create(name='Clase Prueba', code='ABC123', teacher=self.teacher)

    def test_create_assignment(self):
        file_data = SimpleUploadedFile('testfile.pdf', b'contenido de prueba', content_type='application/pdf')
        response = self.client.post('/activities/api/assignment/create/', {
            'title': 'Tarea AJAX',
            'description': 'Descripción de prueba',
            'instructions': 'Instrucciones de prueba',
            'due_date': '2030-12-31T23:59',
            'is_public': 'on',
            'links': 'https://youtube.com/ejemplo',
        },
        format='multipart',
        FILES={'attachments': file_data})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertTrue(Assignment.objects.filter(title='Tarea AJAX').exists())
        tarea = Assignment.objects.get(title='Tarea AJAX')
        self.assertTrue(tarea.is_public)
        # Archivos y links: depende de implementación, omitir si no hay modelo relacionado

    def test_edit_assignment(self):
        assignment = Assignment.objects.create(
            title='Tarea Editar', description='Desc', instructions='Inst', due_date='2030-12-31', author=self.teacher
        )
        response = self.client.post(f'/activities/api/assignment/edit/{assignment.id}/', {
            'title': 'Tarea Editada',
            'description': 'Nueva desc',
            'instructions': 'Nuevas instrucciones'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        assignment.refresh_from_db()
        self.assertEqual(assignment.title, 'Tarea Editada')

    def test_delete_assignment(self):
        assignment = Assignment.objects.create(
            title='Tarea Borrar', description='Desc', instructions='Inst', due_date='2030-12-31', author=self.teacher
        )
        response = self.client.delete(f'/activities/api/assignment/delete/{assignment.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertFalse(Assignment.objects.filter(id=assignment.id).exists())

    def test_assign_to_class(self):
        assignment = Assignment.objects.create(
            title='Tarea Asignar', description='Desc', instructions='Inst', due_date='2030-12-31', author=self.teacher
        )
        response = self.client.post(f'/activities/api/assignment/assign_classes/{assignment.id}/', {
            'classroom_ids': [self.classroom.id]
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        # Verifica que exista la relación ClassroomActivity
        self.assertTrue(ClassroomActivity.objects.filter(classroom=self.classroom, assignment=assignment).exists())

    def test_public_assignment_visibility(self):
        assignment = Assignment.objects.create(
            title='Tarea Pública', description='Desc', instructions='Inst', due_date='2030-12-31', author=self.teacher, is_public=True
        )
        # Simula que otro docente puede ver la tarea pública como plantilla
        other_teacher = User.objects.create_user(username='profe2', email='profe2@example.com', password='test456', user_type=2)
        self.client.login(username='profe2', password='test456')
        response = self.client.get('/activities/api/assignment/public_list/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        titles = [a['title'] for a in data.get('assignments', [])]
        self.assertIn('Tarea Pública', titles)

if __name__ == '__main__':
    import unittest
    unittest.main() 