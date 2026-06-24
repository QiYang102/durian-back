from django.shortcuts import get_object_or_404
from django.db import transaction
from team.models import Team
from .models import Iteration
from iteration.serializers import IterationSerializer
from core.views import BaseDynamicModelViewSet
from rest_framework.response import Response
from story.models import Story
from task.models import Task, TaskHour
from task.serializers import TaskSerializer
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db.models import Subquery, Sum, OuterRef, Max
from rest_framework import status
from django.db.models.functions import TruncDate
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
import json  
from django.shortcuts import get_object_or_404
from django.utils import timezone

class IterationViewSet(BaseDynamicModelViewSet):
    serializer_class = IterationSerializer
    queryset = Iteration.objects.all()
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    @action(methods=['get'], url_path='getLatestIterationId', detail=False)
    def getLatestIterationId(self, request):
        try:
            latest_active_iteration = Iteration.objects.filter(is_active=True).filter(is_active=True).latest('end_date')

            incomplete_task = Task.objects.filter(
                iteration=latest_active_iteration,
                status__in=['do', 'doing'],
                is_active=True
            )

            task_serializer = TaskSerializer(incomplete_task, many=True)

            response_data = {
                'latest_active_iteration_id': latest_active_iteration.id,
                'incomplete_task': task_serializer.data,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Iteration.DoesNotExist:
            return Response({'detail': 'No active iterations found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['post'], url_path='moveTasks', detail=False)
    def moveTasks(self, request):
        try:
            form_data = json.loads(request.data.get('form', '{}'))
            task_ids = request.data.getlist('taskId[]')
            proceed = request.data['proceed']
            previosIterationId = request.data['lastIterationId']
            team = get_object_or_404(Team, pk=int(form_data['team']))
            start_date_str = form_data['start_date']
            end_date_str = form_data['end_date']

            start_date = timezone.make_aware(timezone.datetime.strptime(start_date_str, '%Y-%m-%d'))
            end_date = timezone.make_aware(timezone.datetime.strptime(end_date_str, '%Y-%m-%d'))

            if not form_data:
                return Response({'detail': 'Form data is missing in the request.'}, status=status.HTTP_400_BAD_REQUEST)

            new_iteration = Iteration(
                name=form_data['name'], 
                start_date=start_date,
                end_date=end_date,
                status=form_data['status'],
                team=team,
                tenant=team.tenant
            )

            with transaction.atomic():
                new_iteration.save()

                if proceed:
                    incomplete_tasks = Task.objects.filter(
                        iteration_id=previosIterationId,
                        status__in=['do', 'doing'],
                        is_active=True,
                        id__in=task_ids
                    )
                    
                    if incomplete_tasks.exists():
                        tasks_by_story = {}

                        for task in incomplete_tasks:
                            if task.story_id in tasks_by_story:
                                tasks_by_story[task.story_id].append(task)
                            else:
                                tasks_by_story[task.story_id] = [task]

                        for story_id, tasks in tasks_by_story.items():
                            original_story = tasks[0].story

                            new_story = Story(
                                description=original_story.description,
                                iteration=new_iteration,
                                project=original_story.project,
                                team=original_story.team,
                                tenant=new_iteration.tenant
                            )

                            new_story.save()

                            Task.objects.filter(is_active=True).filter(id__in=[task.id for task in tasks]).update(
                                iteration=new_iteration,
                                story=new_story,
                            )

                            original_story.is_complete = True
                            original_story.save()

            response_data = {
                'message': 'Iteration and tasks moved successfully',
                'new_iteration_id': new_iteration.id
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['post'], url_path='get-daily-progress', detail=False)
    def getDailyProgress(self, request):
        iteration_id = request.data.get('iterationId', 0)
        project_id = request.data.get('projectId', 0)
        # print(iteration_id)

        if iteration_id == '0':
            iteration_id = []
        elif ',' in iteration_id:
            iteration_id = [int(item) for item in iteration_id.split(',')]
        elif iteration_id:
            iteration_id = [int(iteration_id)]

        team_id = get_object_or_404(Team, pk=int(request.data.get('teamId')))
        
        data = {
            'iteration': [],
            'stories': [],
        }

        print(team_id, iteration_id)
        if not iteration_id:
            iteration_object=Iteration.objects.filter(team=team_id, is_active=True).order_by('id').last()
            iteration_data = {
                'id': iteration_object.pk,
                'name': iteration_object.name,
                #'team': iteration_object.team.name
            }
            data['iteration'].append(iteration_data)
            # task_qs=Task.objects.filter(iteration_id=iteration_object.id).filter(is_active=True)
            if project_id == '0':
                task_qs=Task.objects.filter(iteration_id=iteration_object.id).filter(is_active=True)
            else :
                task_qs=Task.objects.filter(iteration_id=iteration_object.id).filter(is_active=True).filter(story__project_id = project_id)
                print('task_qs', task_qs)
        else:
            iteration_object = Iteration.objects.filter(pk__in=list(iteration_id)).filter(is_active=True)
            for iteration in iteration_object:
                iteration_data = {
                    'id': iteration.pk,
                    'name': iteration.name,
                    #'team': iteration.team.name
                }
                data['iteration'].append(iteration_data)
            # task_qs = Task.objects.filter(iteration_id__in=iteration_id, is_bug=False).filter(is_active=True)
            if project_id == '0':
                task_qs = Task.objects.filter(iteration_id__in=iteration_id, is_bug=False).filter(is_active=True)
            else :
                task_qs = Task.objects.filter(iteration_id__in=iteration_id, is_bug=False).filter(is_active=True).filter(story__project_id = project_id)

        task_ids=task_qs.values_list('id', flat=True)

        task_hour_qs=TaskHour.objects.filter(task_id__in=list(task_ids), task__is_active=True)

        # total estimated time of the story
        groupby_story_and_task = task_qs.values('story','story__description','story__team__name').annotate(total_estimated_time=Sum('estimate_time')).order_by('-iteration__id').order_by('-story__id')
        
        # task remain hour of the day
        groupby_task_and_task_hour_date = task_hour_qs.annotate(
            task_date=TruncDate('update_at'),
        ).values('task', 'task_date','task__story','task__description','task__user__fullname','task__estimate_time').annotate(total_remain_hour=Sum('remain_hour')).order_by()
        
        # get latest remain hour of the day
        latest_update_subquery = task_hour_qs.filter(
            task=OuterRef('task'),
            update_at__date=OuterRef('update_at__date')
        ).values('task').annotate(
            latest_update_at=Max('update_at')
        ).values('latest_update_at')

        latest_task_hours = task_hour_qs.filter(
            update_at__in=Subquery(latest_update_subquery)
        ).annotate(task_date=TruncDate('update_at'),).values('task', 'task_date', 'remain_hour','status')

        # Create a dictionary to store the structured data
        result = {}

        for story_entry in groupby_story_and_task:
            story_id = story_entry['story']
            story_data = {
                'story': story_id,
                'description': story_entry['story__description'],
                'total_estimated_time': story_entry['total_estimated_time'],
                'tasks': [],
            }

            # Filter task entries that belong to the current story
            story_tasks = [task_entry for task_entry in groupby_task_and_task_hour_date if task_entry['task__story'] == story_id]

            for task_entry in story_tasks:
                task_data = {
                    'task_id': task_entry['task'],
                    'task_description': task_entry['task__description'],
                    'task_date': task_entry['task_date'],
                    'total_remain_hour': task_entry['total_remain_hour'],
                    'user':task_entry['task__user__fullname'],
                    'status': None,
                    'estimate_time':task_entry['task__estimate_time'],
                    'remain_hour': None,
                }

                for latest_task_entry in latest_task_hours:
                    if (latest_task_entry['task'] == task_entry['task'] and latest_task_entry['task_date'] == task_data['task_date']):
                        task_data['remain_hour'] = latest_task_entry['remain_hour']
                        task_data['status'] = latest_task_entry['status']
                        break

                story_data['tasks'].append(task_data)

            if story_data['tasks']:
                result[story_id] = story_data

        data['stories'] = list(result.values())

        return Response(data)
    
    # return iterations id for select options
    @action(methods=['post'], url_path='get-iteration-options', detail=False)
    def get_iteration_options(self,request):
        team_id = get_object_or_404(Team, pk=int(request.data.get('teamId')))
        iteration_object=Iteration.objects.filter(team=team_id, is_active=True).order_by('-id')

        iterationsDict = [
            {'value': iteration.id, 'label': iteration.name}
            for iteration in iteration_object
        ]
        return Response(iterationsDict)