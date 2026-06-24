from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from core.models import User
from team.models import Team, TeamMember
from iteration.models import Iteration
from task.models import Task
from core.test_utility import setup_test
from story.models import Story

class BugsCountPieChartTest(TestCase):
    def setUp(self):
        self.client, self.user, self.tenant = setup_test()

    def test_bugs_count_pie_chart_without_passing_iteration(self):
        team = Team.objects.create(name="Test Team", tenant=self.tenant)
        user2 = User.objects.create(username='test2',fullname='user2',password='tech1234',tenant=self.tenant)
        team_member_1 = TeamMember.objects.create(team=team,user=self.user,tenant=self.tenant)
        team_member_2 = TeamMember.objects.create(team=team,user=user2,tenant=self.tenant)            
        iteration = Iteration.objects.create(team=team, name="Test Iteration", start_date='2023-10-23', end_date='2023-10-27',tenant=self.tenant)
        story = Story.objects.create(iteration=iteration, description="<p>Test Story</p>", team=team, tenant=self.tenant)
        task1 = Task.objects.create(iteration=iteration,story=story, description="<p>Test Task 1</p>", due_date='2023-10-23T18:00:00', user=self.user, total_hour_used=2, estimate_time=2, tenant=self.tenant,
            is_bug=True)
        task2 = Task.objects.create(iteration=iteration,story=story, description="<p>Test Task 2</p>", due_date='2023-10-23T18:00:00', user=self.user, total_hour_used=2, estimate_time=2, tenant=self.tenant,
            is_bug=True)
        
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.get('http://127.0.0.1:8000/v1/reporting/bugs-count-pie-chart/?iteration=&team='+str(team.pk))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data['result']
        
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['value'], 2)  # Total bug count for the self.user
        self.assertEqual(data[1]['value'], 0) #Total bug count for user2
        self.assertEqual(response.data['total_bugs'],2)

    def test_bugs_count_pie_chart_with_one_iteration(self):
        team = Team.objects.create(name="Test Team", tenant=self.tenant)
        user2 = User.objects.create(username='test2',fullname='user2',password='tech1234',tenant=self.tenant)
        team_member_1 = TeamMember.objects.create(team=team,user=self.user,tenant=self.tenant)
        team_member_2 = TeamMember.objects.create(team=team,user=user2,tenant=self.tenant)            
        iteration = Iteration.objects.create(team=team, name="Test Iteration", start_date='2023-10-23', end_date='2023-10-27',tenant=self.tenant)
        story = Story.objects.create(iteration=iteration, description="<p>Test Story</p>", team=team, tenant=self.tenant)
        task1 = Task.objects.create(iteration=iteration,story=story, description="<p>Test Task 1</p>", due_date='2023-10-23T18:00:00', user=self.user, total_hour_used=2, estimate_time=2, tenant=self.tenant,
            is_bug=True)
        task2 = Task.objects.create(iteration=iteration,story=story, description="<p>Test Task 2</p>", due_date='2023-10-23T18:00:00', user=user2, total_hour_used=2, estimate_time=2, tenant=self.tenant,
            is_bug=True)
        
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.get('http://127.0.0.1:8000/v1/reporting/bugs-count-pie-chart/?iteration='+str(iteration.pk)+'&team='+str(team.pk))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data['result']
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['value'], 1)  # Total bug count for the self.user
        self.assertEqual(data[1]['value'], 1) #Total bug count for user2
        self.assertEqual(response.data['total_bugs'],2)

    def test_bugs_count_pie_chart_with_multiple_iteration(self):
        team = Team.objects.create(name="Test Team", tenant=self.tenant)
        user2 = User.objects.create(username='test2',fullname='user2',password='tech1234',tenant=self.tenant)
        team_member_1 = TeamMember.objects.create(team=team,user=self.user,tenant=self.tenant)
        team_member_2 = TeamMember.objects.create(team=team,user=user2,tenant=self.tenant)            
        iteration1 = Iteration.objects.create(team=team, name="Test Iteration1", start_date='2023-10-23', end_date='2023-10-27',tenant=self.tenant)
        iteration2 = Iteration.objects.create(team=team, name="Test Iteration2", start_date='2023-10-28', end_date='2023-11-5',tenant=self.tenant)
        story1 = Story.objects.create(iteration=iteration1, description="<p>Test Story1</p>", team=team, tenant=self.tenant)
        story2 = Story.objects.create(iteration=iteration2, description="<p>Test Story2</p>", team=team, tenant=self.tenant)
        task1 = Task.objects.create(iteration=iteration1,story=story1, description="<p>Test Task 1</p>", due_date='2023-10-23T18:00:00', user=self.user, total_hour_used=2, estimate_time=2, tenant=self.tenant,
            is_bug=True)
        task2 = Task.objects.create(iteration=iteration2,story=story2, description="<p>Test Task 2</p>", due_date='2023-10-23T18:00:00', user=user2, total_hour_used=2, estimate_time=2, tenant=self.tenant,
            is_bug=True)
        
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.get('http://127.0.0.1:8000/v1/reporting/bugs-count-pie-chart/?iteration='+str(iteration1.pk)+','+str(iteration2.pk)+'&team='+str(team.pk))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data['result']
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['value'], 1)  # Total bug count for the self.user
        self.assertEqual(data[1]['value'], 1) #Total bug count for user2
        self.assertEqual(response.data['total_bugs'],2)

    def test_bugs_count_pie_chart_with_only_one_user_have_bugs_with_multiple_iteration(self):
        team = Team.objects.create(name="Test Team", tenant=self.tenant)
        user2 = User.objects.create(username='test2',fullname='user2',password='tech1234',tenant=self.tenant)
        team_member_1 = TeamMember.objects.create(team=team,user=self.user,tenant=self.tenant)
        team_member_2 = TeamMember.objects.create(team=team,user=user2,tenant=self.tenant)            
        iteration1 = Iteration.objects.create(team=team, name="Test Iteration1", start_date='2023-10-23', end_date='2023-10-27',tenant=self.tenant)
        iteration2 = Iteration.objects.create(team=team, name="Test Iteration2", start_date='2023-10-28', end_date='2023-11-5',tenant=self.tenant)
        story1 = Story.objects.create(iteration=iteration1, description="<p>Test Story1</p>", team=team, tenant=self.tenant)
        story2 = Story.objects.create(iteration=iteration2, description="<p>Test Story2</p>", team=team, tenant=self.tenant)
        task1 = Task.objects.create(iteration=iteration1,story=story1, description="<p>Test Task 1</p>", due_date='2023-10-23T18:00:00', user=self.user, total_hour_used=2, estimate_time=2, tenant=self.tenant,
            is_bug=True)
        task2 = Task.objects.create(iteration=iteration2,story=story2, description="<p>Test Task 2</p>", due_date='2023-10-23T18:00:00', user=self.user, total_hour_used=2, estimate_time=2, tenant=self.tenant,
            is_bug=True)
        
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.get('http://127.0.0.1:8000/v1/reporting/bugs-count-pie-chart/?iteration='+str(iteration1.pk)+','+str(iteration2.pk)+'&team='+str(team.pk))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data['result']
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['value'], 2)  # Total bug count for the self.user
        self.assertEqual(data[1]['value'], 0) #Total bug count for user2
        self.assertEqual(response.data['total_bugs'],2)

    def test_bugs_count_pie_chart_with_invalid_team(self):
        team = Team.objects.create(name="Test Team", tenant=self.tenant)
        user2 = User.objects.create(username='test2',fullname='user2',password='tech1234',tenant=self.tenant)
        team_member_1 = TeamMember.objects.create(team=team,user=self.user,tenant=self.tenant)
        team_member_2 = TeamMember.objects.create(team=team,user=user2,tenant=self.tenant)            
        iteration1 = Iteration.objects.create(team=team, name="Test Iteration1", start_date='2023-10-23', end_date='2023-10-27',tenant=self.tenant)
        iteration2 = Iteration.objects.create(team=team, name="Test Iteration2", start_date='2023-10-28', end_date='2023-11-5',tenant=self.tenant)
        story1 = Story.objects.create(iteration=iteration1, description="<p>Test Story1</p>", team=team, tenant=self.tenant)
        story2 = Story.objects.create(iteration=iteration2, description="<p>Test Story2</p>", team=team, tenant=self.tenant)
        task1 = Task.objects.create(iteration=iteration1,story=story1, description="<p>Test Task 1</p>", due_date='2023-10-23T18:00:00', user=self.user, total_hour_used=2, estimate_time=2, tenant=self.tenant,
            is_bug=True)
        task2 = Task.objects.create(iteration=iteration2,story=story2, description="<p>Test Task 2</p>", due_date='2023-10-23T18:00:00', user=self.user, total_hour_used=2, estimate_time=2, tenant=self.tenant,
            is_bug=True)
        
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.get('http://127.0.0.1:8000/v1/reporting/bugs-count-pie-chart/?iteration='+str(iteration1.pk)+','+str(iteration2.pk)+'&team=2')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data['result']
        self.assertEqual(len(data), 0)
        self.assertEqual(response.data['total_bugs'],0)

    def test_bugs_count_pie_chart_without_passing_team(self):
        team = Team.objects.create(name="Test Team", tenant=self.tenant)
        user2 = User.objects.create(username='test2',fullname='user2',password='tech1234',tenant=self.tenant)
        team_member_1 = TeamMember.objects.create(team=team,user=self.user,tenant=self.tenant)
        team_member_2 = TeamMember.objects.create(team=team,user=user2,tenant=self.tenant)            
        iteration1 = Iteration.objects.create(team=team, name="Test Iteration1", start_date='2023-10-23', end_date='2023-10-27',tenant=self.tenant)
        iteration2 = Iteration.objects.create(team=team, name="Test Iteration2", start_date='2023-10-28', end_date='2023-11-5',tenant=self.tenant)
        story1 = Story.objects.create(iteration=iteration1, description="<p>Test Story1</p>", team=team, tenant=self.tenant)
        story2 = Story.objects.create(iteration=iteration2, description="<p>Test Story2</p>", team=team, tenant=self.tenant)
        task1 = Task.objects.create(iteration=iteration1,story=story1, description="<p>Test Task 1</p>", due_date='2023-10-23T18:00:00', user=self.user, total_hour_used=2, estimate_time=2, tenant=self.tenant,
            is_bug=True)
        task2 = Task.objects.create(iteration=iteration2,story=story2, description="<p>Test Task 2</p>", due_date='2023-10-23T18:00:00', user=self.user, total_hour_used=2, estimate_time=2, tenant=self.tenant,
            is_bug=True)
        
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.get('http://127.0.0.1:8000/v1/reporting/bugs-count-pie-chart/?iteration='+str(iteration1.pk)+','+str(iteration2.pk)+'&team=')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_bugs_count_pie_chart_with_unauthorized_user(self):
        team = Team.objects.create(name="Test Team", tenant=self.tenant)
        user2 = User.objects.create(username='test2',fullname='user2',password='tech1234',tenant=self.tenant)
        team_member_1 = TeamMember.objects.create(team=team,user=self.user,tenant=self.tenant)
        iteration1 = Iteration.objects.create(team=team, name="Test Iteration1", start_date='2023-10-23', end_date='2023-10-27',tenant=self.tenant)
        story1 = Story.objects.create(iteration=iteration1, description="<p>Test Story1</p>", team=team, tenant=self.tenant)
        task1 = Task.objects.create(iteration=iteration1,story=story1, description="<p>Test Task 1</p>", due_date='2023-10-23T18:00:00', user=self.user, total_hour_used=2, estimate_time=2, tenant=self.tenant,
            is_bug=True)
        
        client = APIClient()
        client.force_authenticate(user=None)
        response = client.get('http://127.0.0.1:8000/v1/reporting/bugs-count-pie-chart/?iteration='+str(iteration1.pk)+'&team=2')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
