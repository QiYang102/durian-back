from django.shortcuts import get_object_or_404, render
from core import utility
from core.views import BaseDynamicModelViewSet
from story.models import Story
from .models import Task, TaskHour, TaskImage, TaskTemplate, TaskTemplateItem
from task.serializers import TaskHourSerializer, TaskImageSerializer, TaskSerializer, TaskTemplateItemSerializer, TaskTemplateSerializer
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

class TaskViewSet(BaseDynamicModelViewSet):
    serializer_class = TaskSerializer
    queryset = Task.objects.all()
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_queryset(self):
        qs = Task.objects.all()

        iteration_id = self.request.query_params.get("iteration_id")

        if iteration_id:
            qs = qs.filter(story__iteration=iteration_id)
        return qs

    @action(methods=['post'], url_path='toggle-issue', detail=True)
    def toggle_issue(self, request, pk=None):
        """Toggle task between complete and do status"""
        try:
            task = self.get_object()
            
            is_completing = task.status != Task.STATUS_COMPLETE
            task.status = Task.STATUS_COMPLETE if is_completing else Task.STATUS_DO
            task.save()
            
            if task.is_bug and task.story:
                task.story.issue_resolved_at = timezone.now() if is_completing else None
                task.story.save()
            
            return Response({
                'task_id': task.id,
                'task_status': task.status,
                'is_complete': is_completing
            }, status=status.HTTP_200_OK)
            
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TaskHourViewSet(BaseDynamicModelViewSet):
    serializer_class = TaskHourSerializer
    queryset = TaskHour.objects.all()
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

class TaskImageViewSet(BaseDynamicModelViewSet):
    serializer_class = TaskImageSerializer
    queryset = TaskImage.objects.all()
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    
    @action(methods=['post'], url_path='uploadImage', detail=False)
    def uploadImage(self, request):
        try:
            task_id = request.data['task_id']
            task = get_object_or_404(Task,pk=int(task_id))
            if request.data['image']:
                image_data = request.data['image']

                image_data= utility.resize_image(
                    image_data, max_size_kb=300, max_dimension_pixel=1200
                )
                task_image = TaskImage(task=task, image=image_data, tenant=task.tenant)
                task_image.save()

                return Response({'message': 'Image uploaded successfully'}, status=status.HTTP_201_CREATED)
            
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

class TaskTemplateViewSet(BaseDynamicModelViewSet):
    serializer_class = TaskTemplateSerializer
    queryset = TaskTemplate.objects.all()
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    # return template for select options
    @action(methods=['get'], url_path='get-template-options', detail=False)
    def get_template_options(self,request):
        template_object=TaskTemplate.objects.filter(is_active=True)
        
        templateDict = [
            {'value': template.pk, 'label': template.name}
            for template in template_object
        ]
        return Response(templateDict)
  
class TaskTemplateItemViewSet(BaseDynamicModelViewSet):
    serializer_class = TaskTemplateItemSerializer
    queryset = TaskTemplateItem.objects.all()
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']  

    @action(methods=['post'], url_path='create-task-by-template', detail=False)
    def create_task_by_template(self,request):
        template_id = request.data.get('templateId', 0)
        story_id = request.data.get('storyId',0)
        if ',' in template_id:
            template_id = [int(item) for item in template_id.split(',')]
        elif template_id:
            template_id = [int(template_id)]

        if story_id:
            template_items = TaskTemplateItem.objects.filter(task_template__id__in=template_id, is_active=True).order_by('ordering')
            story = Story.objects.get(pk=story_id)
            for template_item in template_items:
                description = "<p>"+template_item.description+"</p>"
                task_qs = Task.objects.create(story=story, description=description, iteration=story.iteration, estimate_time=template_item.estimate_time, tenant=story.tenant)
            return Response({'message': 'Tasks created successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'Story not found'}, status=status.HTTP_400_BAD_REQUEST)


