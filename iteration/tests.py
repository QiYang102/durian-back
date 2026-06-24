from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.test_utility import setup_test
from django.db import transaction

from iteration.models import Iteration
from story.models import Story
from task.models import Task, TaskHour
from team.models import Team

# Create your tests here.
class DailyProgressTestCase(TestCase):
    def setUp(self):
        self.client, self.user, self.tenant = setup_test()

    def test_get_daily_progress(self):
        with transaction.atomic():
            team = Team.objects.create(name="Test Team", tenant=self.tenant)
            iteration = Iteration.objects.create(team=team, name="Test Iteration", start_date='2023-10-23', end_date='2023-10-27',tenant=self.tenant)
            story = Story.objects.create(iteration=iteration, description="<p>Test Story</p>", team=team, tenant=self.tenant)
            task = Task.objects.create(iteration=iteration,story=story, description="<p>Test Task</p>", due_date='2023-10-23T18:00:00', user=self.user, total_hour_used=2, estimate_time=2, tenant=self.tenant)
            task_hour = TaskHour.objects.create(task=task, hour=2, remain_hour=1, status='slow', user=self.user, tenant=self.tenant)

        data = {
            'teamId': team.pk,
            'iterationId': iteration.pk,
        }

        response = self.client.post('/v1/iterations/get-daily-progress', data, format='json')

        self.assertEqual(response.status_code, 200)

        self.assertIsNotNone(response.data)

        self.assertIn('iteration', response.data)
        self.assertIn('stories', response.data)
        self.assertIsInstance(response.data['stories'], list)
        
        self.assertEqual(response.data['iteration'][0]['id'], iteration.pk)
        self.assertEqual(response.data['stories'][0]['story'], story.pk)
        self.assertEqual(response.data['stories'][0]['tasks'][0]['task_id'], task.pk)
        self.assertEqual(response.data['stories'][0]['tasks'][0]['remain_hour'],task_hour.remain_hour)
        self.assertEqual(response.data['stories'][0]['tasks'][0]['user'], self.user.fullname)

    def test_get_daily_progress_without_passing_iterationId(self):
        with transaction.atomic():
            team = Team.objects.create(name="Test Team", tenant=self.tenant)
            iteration = Iteration.objects.create(team=team, name="Test Iteration", start_date='2023-10-23', end_date='2023-10-27',tenant=self.tenant)
            story = Story.objects.create(iteration=iteration, description="<p>Test Story</p>", team=team, tenant=self.tenant)
            task = Task.objects.create(iteration=iteration,story=story, description="<p>Test Task</p>", due_date='2023-10-23T18:00:00', user=self.user, total_hour_used=2, estimate_time=2, tenant=self.tenant)
            task_hour = TaskHour.objects.create(task=task, hour=2, remain_hour=1, status='slow', user=self.user, tenant=self.tenant)

        data = {
            'teamId': team.pk,
            'iterationId': '',
        }

        response = self.client.post('/v1/iterations/get-daily-progress', data, format='json')

        self.assertEqual(response.status_code, 200)

        self.assertIsNotNone(response.data)

        self.assertIn('iteration', response.data)
        self.assertIn('stories', response.data)
        self.assertIsInstance(response.data['stories'], list)
        
        self.assertEqual(response.data['iteration'][0]['id'], iteration.pk)
        self.assertEqual(response.data['stories'][0]['story'], story.pk)
        self.assertEqual(response.data['stories'][0]['tasks'][0]['task_id'], task.pk)
        self.assertEqual(response.data['stories'][0]['tasks'][0]['remain_hour'],task_hour.remain_hour)
        self.assertEqual(response.data['stories'][0]['tasks'][0]['user'], self.user.fullname)

    def test_get_daily_progress_team_not_exists(self):
        with transaction.atomic():
            team = Team.objects.create(name="Test Team", tenant=self.tenant)
            iteration = Iteration.objects.create(team=team, name="Test Iteration", start_date='2023-10-23', end_date='2023-10-27',tenant=self.tenant)
            story = Story.objects.create(iteration=iteration, description="<p>Test Story</p>", team=team, tenant=self.tenant)
            task = Task.objects.create(iteration=iteration,story=story, description="<p>Test Task</p>", due_date='2023-10-23T18:00:00', user=self.user, total_hour_used=2, estimate_time=2, tenant=self.tenant)
            task_hour = TaskHour.objects.create(task=task, hour=2, remain_hour=1, status='slow', user=self.user, tenant=self.tenant)

        data = {
            'teamId': '2',
            'iterationId': '',
        }

        response = self.client.post('/v1/iterations/get-daily-progress', data, format='json')

        self.assertNotEqual(response.status_code, 200)
    
    def test_get_daily_progress_no_tasks(self):
        with transaction.atomic():
            team = Team.objects.create(name="Test Team", tenant=self.tenant)
            iteration = Iteration.objects.create(team=team, name="Test Iteration", start_date='2023-10-23', end_date='2023-10-27', tenant=self.tenant)
            story = Story.objects.create(iteration=iteration, description="<p>Test Story</p>", team=team, tenant=self.tenant)

        data = {
            'teamId': team.pk,
            'iterationId': iteration.pk,
        }

        response = self.client.post('/v1/iterations/get-daily-progress', data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['stories']), 0)