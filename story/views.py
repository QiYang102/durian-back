from datetime import timedelta
from django.shortcuts import get_object_or_404, render
from core import utility
from story import story_service
from story.serializers import TagSerializer, StoryImageSerializer, StoryProjectSerializer, StorySerializer, VerifiedByUserSerializer, TagItemSerializer
from story.models import Tag, Story, StoryImage, VerifiedByUser, TagItem
from core.views import BaseDynamicModelViewSet
from iteration.models import Iteration
from story.story_service import check_should_celebrate, get_incomplete_story, get_my_task_story
from task.models import Task
from rest_framework.response import Response
from rest_framework.decorators import action
from dynamic_rest.viewsets import DynamicModelViewSet
from rest_framework import status, filters
from django.db.models import Q, Sum
from django.utils import timezone

# Create your views here.
class StoryViewSet(BaseDynamicModelViewSet):
    filter_backends = list(DynamicModelViewSet.filter_backends) + [filters.SearchFilter]
    serializer_class = StorySerializer
    queryset = Story.objects.all()
    http_method_names = ['get','post', 'put', 'patch','delete']
    search_fields = ('parent_story__name','name', 'short_description',)

    def get_queryset(self):
        qs = Story.objects.all()

        user_id = self.request.query_params.get("user_id")

        if user_id:
            qs = qs.filter(task__user=user_id).distinct()
        return qs
    
    @action(methods=['get'], url_path='get-incomplete-story', detail=False)
    def get_incomplete_story(self, request):
        try:
            #user = request.user
            user = request.query_params.get('user')
            iteration = request.query_params.get('iteration')
            
            incomplete_stories = get_incomplete_story(user, iteration) 

            story_serializer = StoryProjectSerializer(incomplete_stories, many=True)

            return Response(story_serializer.data)

        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(methods=['get'], url_path='get-my-task-story', detail=False)
    def get_my_task_story(self, request):
        try:
            #user = request.user
            user = request.query_params.get('user')
            iteration = request.query_params.get('iteration')

            # write new function 
            incomplete_task = get_my_task_story(user, iteration) 

            story_serializer = StorySerializer(incomplete_task, many=True)

            return Response(story_serializer.data)

        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)    

    @action(methods=['get'], url_path='check-celebration', detail=False)
    def check_celebration(self, request):
        try:
            iteration = request.query_params.get('iteration')

            if not iteration:
                return Response(
                    {'error': 'iteration is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                        
            result = check_should_celebrate(iteration)
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(methods=['post'], url_path='publish', detail=True)
    def publish(self, request, pk=None):
        try:
            story = self.get_object()
            
            if story.status != Story.STATUS_DRAFT:
                return Response(
                    {'error': 'Only draft stories can be published'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not story.description or not story.name:
                return Response(
                    {'error': 'Story must have name and description before publishing'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            story.status = Story.STATUS_NEW
            story.save()
            
            serializer = StorySerializer(story)
            return Response(serializer.data)
            
        except Story.DoesNotExist:
            return Response({'error': 'Story not found'}, status=status.HTTP_404_NOT_FOUND)
        
    @action(methods=['patch'], url_path='move-to-latest-iteration', detail=True)
    
    def move_to_latest_iteration(self, request, pk=None):
        """Move a story to the latest active iteration of its team"""
        try:
            story = self.get_object()
            
            if not story.team:
                return Response(
                    {'detail': 'Story must have a team assigned'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            latest_iteration = Iteration.objects.filter(
                team=story.team,
                is_active=True
            ).latest('end_date')
            
            story.iteration = latest_iteration
            story.save()
            
            serializer = StorySerializer(story)
            
            return Response({
                'story': serializer.data,
                'iteration_id': latest_iteration.id,
                'iteration_name': latest_iteration.name,
                'message': 'Story moved successfully'
            }, status=status.HTTP_200_OK)
            
        except Iteration.DoesNotExist:
            return Response(
                {'detail': 'No active iteration found for this team'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(methods=['get'], url_path='deployment-to-be-deploy', detail=False)
    def get_stories_to_be_deploy(self, request):
        team_id = request.query_params.get('filter{team}') 
        
        if team_id:
            Response({'error': 'team id is required'})

        stories = self.get_queryset().filter(
            is_needed_to_deploy=True,
            deployment_status=Story.DEPLOYMENT_PENDING,
            team=team_id,
            is_active=True
        )
        serializer = self.get_serializer(stories, many=True)
        return Response(serializer.data)

    @action(methods=['get'], url_path='deployment-staging', detail=False)
    def get_stories_in_staging(self, request):
        team_id = request.query_params.get('filter{team}') 
        
        if team_id:
            Response({'error': 'team id is required'})

        stories = self.get_queryset().filter(
            is_needed_to_deploy=True,
            deployment_status=Story.DEPLOYMENT_STAGING,
            team=team_id,
            is_active=True
        )
        serializer = self.get_serializer(stories, many=True)
        return Response(serializer.data)

    @action(methods=['get'], url_path='deployment-production', detail=False)
    def get_stories_in_production(self, request):
        team_id = request.query_params.get('filter{team}') 
        
        if team_id:
            Response({'error': 'team id is required'})
            
        two_weeks_ago = timezone.now() - timedelta(weeks=2)

        stories = self.get_queryset().filter(
            is_needed_to_deploy=True,
            deployment_status=Story.DEPLOYMENT_PRODUCTION,
            team=team_id,
            is_active=True
        ).filter(
            Q(deployment_production_status_at__gte=two_weeks_ago) | Q(has_issue=True)
        )
        serializer = self.get_serializer(stories, many=True)
        return Response(serializer.data)
    
    @action(methods=['get'], url_path='storyboard-counts', detail=False)
    def get_storyboard_counts(self, request):
        try:
            iteration_id = request.query_params.get('iteration')
            
            if not iteration_id:
                return Response(
                    {'error': 'iteration is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            iteration = get_object_or_404(Iteration, pk=iteration_id)
            
            incompleted_count = Story.objects.filter(
                iteration_id=iteration_id,
                status__in=[Story.STATUS_NEW, Story.STATUS_STARTED, Story.STATUS_TAKEN],
                is_active=True
            ).count()
            
            completed_count = Story.objects.filter(
                iteration_id=iteration_id,
                status=Story.STATUS_COMPLETED,
                is_active=True
            ).count()
            
            today = timezone.now().date()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
            issues_count = Task.objects.filter(
                is_bug=True,
                create_at__date__gte=start_of_week,
                create_at__date__lte=end_of_week,
                is_active=True
            ).count()
            
            return Response({
                'incompleted': incompleted_count,
                'completed': completed_count,
                'issues': issues_count
            }, status=status.HTTP_200_OK)
            
        except Iteration.DoesNotExist:
            return Response(
                {'error': 'Iteration not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 
    
    @action(methods=['get'], url_path='tags', detail=True)
    def get_story_tags(self, request, pk=None):
        """
        Get tags list
        """
        story = self.get_object()
        
        tags = story.tags.all()
        
        serializer = TagSerializer(tags, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['post'], url_path='add-tag', detail=True)
    def add_tag(self, request, pk=None):
        """
        Create tag
        ----------
        Payload: { "name": "Bug", "color": "info" }
        If exist tag in Tag table then add to the story
        Else create new tag and add to the story
        """
        story = self.get_object()
        tag_name = request.data.get('name')
        tag_color = request.data.get('color', 'info')
        project_id = story.project_id
        team_id = story.team_id
        tenant_id = story.tenant_id

        if not tag_name:
            return Response(
                {'error': 'Tag name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tag_instance = Tag.objects.filter(name__iexact=tag_name, project_id=project_id, team_id=team_id).first()

        if tag_instance:
            print(f"--- Attributes for Tag ID {tag_instance.id} ---")
            for field in tag_instance._meta.fields:
                value = getattr(tag_instance, field.name)
                print(f"{field.name}: {value}")
        else:
            print("Tag instance is None (Not found)")

        if not tag_instance:
            tag_instance = Tag.objects.create(
                name=tag_name,
                color=tag_color,
                project_id=project_id,
                team_id= team_id,
                tenant_id=tenant_id
            )

        if story.tags.filter(id=tag_instance.id).exists():
            return Response(
                {'error': 'Tag already in the story'}, 
                status=status.HTTP_409_CONFLICT
            )
        else:
            story.tags.add(tag_instance)

        return Response(
            TagSerializer(tag_instance).data, 
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], url_path="remove-tag", detail=True)
    def remove_tag(self, request, pk=None):
        """
        Remove tag
        ----------
        Payload { "id": 1 }
        """
        story = self.get_object()
        tag_id = request.data.get('id')

        try:
            tag = Tag.objects.get(id=tag_id)
            story.tags.remove(tag)
            return Response(status=status.HTTP_200_OK)
        except Tag.DoesNotExist:
            return Response({'error': 'Tag not found'}, status=status.HTTP_400_BAD_REQUEST)
    
        
class StoryImageViewSet(BaseDynamicModelViewSet):
    serializer_class = StoryImageSerializer
    queryset = StoryImage.objects.all()
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    
    @action(methods=['post'], url_path='storyUploadImage', detail=False)
    def storyUploadImage(self, request):
        try:
            story_id = request.data['story_id']
            story = get_object_or_404(Story,pk=int(story_id))
            if request.data['image']:
                image_data = request.data['image']

                image_data= utility.resize_image(
                    image_data, max_size_kb=300, max_dimension_pixel=1200
                )
                story_image = StoryImage(story=story, image=image_data, tenant=story.tenant)
                story_image.save()

                return Response({'message': 'Image uploaded successfully'}, status=status.HTTP_201_CREATED)
            
        except Story.DoesNotExist:
            return Response({'error': 'Story not found'}, status=status.HTTP_404_NOT_FOUND)
        
class VerifiedByUserViewSet(BaseDynamicModelViewSet):
    serializer_class = VerifiedByUserSerializer
    queryset = VerifiedByUser.objects.all()
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

class TagViewSet(BaseDynamicModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    filter_backends = list(DynamicModelViewSet.filter_backends) + [filters.SearchFilter]
    search_fields = ['name']
    http_method_names = ['get','post', 'put', 'patch','delete']

    def update(self, request, *args, **kwargs):
        """
        Override update to check for duplicates before saving
        """
        instance = self.get_object()
        
        new_name = request.data.get('name', '').strip()
        
        # Only check if a name was actually provided and it's different
        if new_name and new_name.lower() != instance.name.lower():
            
            # Check if a DIFFERENT tag exists with this name & project
            is_duplicate = Tag.objects.filter(
                name__iexact=new_name,
                project_id=instance.project_id
            ).exclude(id=instance.id).exists()

            if is_duplicate:
                return Response(
                    {'error': f"Tag '{new_name}' already exists in this project."},
                    status=status.HTTP_409_CONFLICT
                )
            
        return super().update(request, *args, **kwargs)

    @action(['get'], url_path='get-tag-report', detail=True)
    def get_tag_report(self, request, pk=None):
        tag_id = pk
        
        tag_items_qs = TagItem.objects.filter(tag_id=tag_id)
        
        total_stories = tag_items_qs.count()

        story_ids = tag_items_qs.values_list('story_id', flat=True)
        stories = Story.objects.filter(
            id__in=story_ids
        ).values(
            "id", "name", "total_estimate_time", "status"
        )

        aggregation = stories.aggregate(
            total_time=Sum('total_estimate_time')
        )
        
        total_estimate_time_sum = aggregation['total_time'] or 0

        tag_items_data = tag_items_qs.values("id", "tag_id", "story_id")

        result = {
            "total_stories": total_stories,
            "total_estimate_hours": total_estimate_time_sum,
            "tag-items": list(tag_items_data),
            "stories": list(stories)
        }

        return Response({'result': result}, status=status.HTTP_200_OK)
    
class TagItemViewSet(DynamicModelViewSet):
    serializer_class = TagItemSerializer
    queryset = TagItem.objects.all()
    filter_backends = list(DynamicModelViewSet.filter_backends) + [filters.SearchFilter]
    http_method_names = ['get','post', 'put', 'patch','delete']
