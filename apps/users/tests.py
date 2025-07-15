from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Child, Suggestion, EducationalResource
from datetime import date

User = get_user_model()

class ParentDashboardAjaxTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.parent = User.objects.create_user(username='parent1', email='parent1@example.com', password='testpass', user_type=3)
        self.client.login(username='parent1', password='testpass')

    def test_add_child_ajax(self):
        url = reverse('users:ajax_add_child')
        data = {
            'child_name': 'Juanito Pérez',
            'child_grade': '1',
            'child_birthdate': '2015-05-10',
            'child_document': '12345678'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.json())
        self.assertTrue(response.json()['success'])
        self.assertTrue(Child.objects.filter(parent=self.parent, name='Juanito Pérez').exists())

    def test_delete_child_ajax(self):
        child = Child.objects.create(parent=self.parent, name='Ana López', grade='2', birthdate=date(2014, 7, 20))
        url = reverse('users:ajax_delete_child')
        response = self.client.post(url, {'child_id': child.id})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertFalse(Child.objects.filter(id=child.id).exists())

    def test_children_list_ajax(self):
        Child.objects.create(parent=self.parent, name='Pepe', grade='1', birthdate=date(2015, 1, 1))
        url = reverse('users:ajax_children_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertIn('html', response.json())
        self.assertIn('Pepe', response.json()['html'])

    def test_send_suggestion_ajax(self):
        url = reverse('users:ajax_send_suggestion')
        data = {
            'type': 'activity',
            'description': 'Sería bueno más juegos interactivos.'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertTrue(Suggestion.objects.filter(parent=self.parent, description__icontains='juegos').exists())

    def test_suggestions_list_ajax(self):
        Suggestion.objects.create(parent=self.parent, type='resource', description='Agregar videos', status='pending')
        url = reverse('users:ajax_suggestions_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertIn('Agregar videos', response.json()['html'])

    def test_educational_resources_ajax(self):
        EducationalResource.objects.create(title='Video de Ciencias', description='Un video educativo', url='http://example.com/video', type='video', grade='1')
        url = reverse('users:ajax_educational_resources')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertIn('Video de Ciencias', response.json()['html'])
