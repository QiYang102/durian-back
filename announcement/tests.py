from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from core.models import User
from team.models import Team
from .models import Announcement


class AnnouncementModelTest(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test team
        self.team = Team.objects.create(
            name='Test Team',
            is_active=True
        )
        
    def test_create_announcement(self):
        """Test creating an announcement"""
        announcement = Announcement.objects.create(
            name='Test Announcement',
            team=self.team,
            created_by=self.user,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=7),
            description='This is a test announcement',
            is_live=True
        )
        
        self.assertEqual(announcement.name, 'Test Announcement')
        self.assertEqual(announcement.team, self.team)
        self.assertEqual(announcement.created_by, self.user)
        self.assertTrue(announcement.is_live)
        
    def test_announcement_str(self):
        """Test the string representation of announcement"""
        announcement = Announcement.objects.create(
            name='Test Announcement',
            team=self.team,
            created_by=self.user,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=7),
            description='Test description',
            is_live=False
        )
        
        expected_str = f'Test Announcement - {self.team.name}'
        self.assertEqual(str(announcement), expected_str)