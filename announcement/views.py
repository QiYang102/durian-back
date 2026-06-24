from django.shortcuts import render
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response


from core.views import BaseDynamicModelViewSet
from .models import Announcement
from .serializers import AnnouncementSerializer


class AnnouncementViewSet(BaseDynamicModelViewSet):
    serializer_class = AnnouncementSerializer
    queryset = Announcement.objects.all()
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def perform_create(self, serializer):
        # Automatically set the created_by field and tenant to the current user
        tenant = getattr(self.request.user, 'tenant', None)
        serializer.save(created_by=self.request.user, tenant=tenant)

    @action(methods=['get'], url_path='live', detail=False)
    def live_announcements(self, request):
        """Get all live announcements"""
        live_announcements = Announcement.objects.live()
        serializer = self.get_serializer(live_announcements, many=True)
        return Response(serializer.data)
    
    