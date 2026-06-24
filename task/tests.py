from django.test import TestCase
from core.test_utility import setup_test
from rest_framework.test import APIClient
from rest_framework import status

from task.models import TaskTemplate

class GetTemplateOptionsTest(TestCase):
    def setUp(self):
        self.client, self.user, self.tenant = setup_test()
    
    def test_get_template_options(self):

        # Create some TaskTemplate objects
        template1 = TaskTemplate.objects.create(name='Template 1', tenant=self.tenant)
        template2 = TaskTemplate.objects.create(name='Template 2', tenant=self.tenant)

        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.get('http://127.0.0.1:8000/v1/task-templates/get-template-options')

        expected_data = [
            {'value': template1.pk, 'label': template1.name},
            {'value': template2.pk, 'label': template2.name},
        ]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)
