from django.shortcuts import render
from core.views import BaseDynamicModelViewSet
from project.models import Project
from project.serializers import ProjectSerializer
from rest_framework import filters
from rest_framework.response import Response
from rest_framework.decorators import action

# Create your views here.
class ProjectViewSet(BaseDynamicModelViewSet):
    filter_backends = list(BaseDynamicModelViewSet.filter_backends) + [filters.SearchFilter]
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()
    http_method_names = ['get','post', 'put', 'patch','delete']
    search_fields = ['id','name']
