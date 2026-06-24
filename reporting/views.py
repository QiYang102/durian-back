from datetime import datetime, timedelta
from collections import defaultdict

import pytz

from django.db.models import F, Sum
from django.db.models.aggregates import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from dynamic_rest.viewsets import DynamicModelViewSet

from core.models import User
from eventcalendar.models import EventCalendar
from iteration.models import Iteration
from reporting import reporting_service
from reporting.models import Season
from reporting.serializers import SeasonSerializer
from story.models import Story, VerifiedByUser
from story.serializers import StorySerializer
from task.models import Task, TaskHour
from team.models import Team, TeamMember
from decimal import Decimal



# Create your views here.
class SeasonViewSet(DynamicModelViewSet):
    serializer_class = SeasonSerializer
    queryset = Season.objects.all()
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_task_statistics(request):
    """
    Get task statistics per user
    Query params:
        - iteration: filter by iteration ID (optional)
        - team: filter by team ID (optional)
    """
    iteration_id = request.query_params.get('iteration')
    team_id = request.query_params.get('team')
    user_id = request.query_params.get('user_id')
    
    result = reporting_service.get_user_task_statistics(
        iteration_id=iteration_id,
        team_id=team_id,
        user_id=user_id,
    )
    
    return Response({'result': result})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def velocity_chart(request):
    """
    Dashboard - Summary
    """
    user = request.user
    team = request.query_params.get('team')

    # total num story, total hour add, iteration name
    result = []
    iteration_queryset = Iteration.objects.filter(team=team).filter(is_active=True)
    for iteration in iteration_queryset:
        dictionary = {}
        dictionary['name'] = iteration.name
        story_queryset = Story.objects.filter(is_active=True).filter(iteration=iteration)
        total_story_count = story_queryset.count()
        dictionary['story'] = total_story_count
        task_ids = Task.objects.filter(is_active=True).filter(iteration=iteration).values_list('id', flat=True)
        total_task_hour = TaskHour.objects.filter(is_active=True).filter(task__in=task_ids).aggregate(Sum('hour'))['hour__sum'] or 0
        dictionary['hour_used'] = total_task_hour
        result.append(dictionary)

    return Response({'result': result})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def hours_burndown_chart(request):
    iteration_id = request.query_params.get('iteration')
    result = []

    # Fetch tasks in iteration
    task_queryset = Task.objects.filter(iteration=iteration_id, is_active=True)
    task_ids = list(task_queryset.values_list('id', flat=True))
    task_estimates = {task.id: task.estimate_time or Decimal('0') for task in task_queryset}

    # Fetch iteration dates
    current_iteration = Iteration.objects.filter(id=iteration_id, is_active=True).first()
    start_date = datetime.strptime(str(current_iteration.start_date), "%Y-%m-%d")
    end_date = datetime.strptime(str(current_iteration.end_date), "%Y-%m-%d")

    timezone = pytz.timezone('Asia/Kuala_Lumpur')
    today = datetime.now(timezone).date()

    # Build day array: day 0 + each date
    day_array = ['day 0']
    current_day = start_date
    day_count = 0
    while current_day <= end_date and day_count < 5:
        day_array.append(current_day.strftime('%Y-%m-%d'))
        current_day += timedelta(days=1)
        day_count += 1

    # Fetch TaskHours
    task_hours_latest = TaskHour.objects.filter(
        is_active=True,
        task__in=task_ids,
        create_at__gte=start_date,
        create_at__lte=end_date
    ).order_by('task_id', 'create_at')

    # Map task_id -> day -> remain_hour
    task_hours_dict = defaultdict(dict)
    for th in task_hours_latest:
        task_hours_dict[th.task_id][th.create_at.date()] = th.remain_hour

    # Build day_remain_dict (each day isolated)
    day_remain_dict = {}

    for i, day in enumerate(day_array):
        if i == 0:
            # Day 0 = total estimate of day 1
            day_1_date = datetime.strptime(day_array[1], '%Y-%m-%d').date()
            # Filter tasks created on or before day 1
            tasks_on_day1_queryset = task_queryset.filter(create_at__date__lte=day_1_date)
            total_estimate_day0 = sum(task.estimate_time or Decimal('0') for task in tasks_on_day1_queryset)
            day_remain_dict['day 0'] = total_estimate_day0

        else:
            day_date = datetime.strptime(day, '%Y-%m-%d').date()
            if day_date > today:
                total_remain = Decimal('0')
            else:
                total_remain = Decimal('0')
                for task_id in task_ids:
                    task_obj = task_queryset.get(id=task_id)
                    if task_obj.create_at.date() > day_date:
                        continue  # task not exist yet
                    remain_hours = task_hours_dict.get(task_id, {}).get(day_date)
                    if remain_hours is not None:
                        total_remain += remain_hours
                    elif task_obj.create_at.date() == day_date:
                        total_remain += task_obj.estimate_time or Decimal('0')
            day_remain_dict[day] = total_remain

    # Prepare chart lines
    hour_types = ['ideal', 'actual']
    total_day0 = day_remain_dict['day 0']
    total_days = len(day_array) - 1  # exclude day 0

    for h_type in hour_types:
        dictionary = {'id': h_type, 'data': []}

        if h_type == 'ideal':
            # Find the first day with non-zero total estimate
            first_nonzero_index = None
            for i, day in enumerate(day_array[1:], start=1):  # skip day 0
                if day_remain_dict.get(day, Decimal('0')) > 0:
                    first_nonzero_index = i
                    break

            if first_nonzero_index is None:
                # No work at all, ideal line all zeros
                for i, day in enumerate(day_array):
                    dictionary['data'].append({'x': f'day {i}', 'y': 0})
            else:
                if first_nonzero_index == 1:
                    # Condition 1: Day 1 working → linear slope from Day 0 to last day
                    first_work_day_index = 0  # slope starts from Day 0
                    day0_start = True
                else:
                    # Condition 2: first working day later → slope starts from first working day
                    first_work_day_index = first_nonzero_index
                    day0_start = False

                # Total estimate of first working day
                first_work_day_date = datetime.strptime(day_array[first_nonzero_index], "%Y-%m-%d").date()
                tasks_on_first_day = task_queryset.filter(create_at__date__lte=first_work_day_date)
                total_work = float(sum(task.estimate_time or Decimal('0') for task in tasks_on_first_day))

                # Total number of days from slope start to last day
                total_days = len(day_array) - first_work_day_index - 1

                for i, day in enumerate(day_array):
                    if i < first_work_day_index:
                        # Days before slope start
                        remaining = 0
                    elif total_days == 0:
                        remaining = 0
                    else:
                        # Linear decrease from slope start to last day
                        remaining = total_work * (total_days - (i - first_work_day_index)) / total_days
                    if remaining < 0:
                        remaining = 0
                    dictionary['data'].append({'x': f'day {i}', 'y': round(remaining, 2)})


        else:
            # Actual line: isolated days, future days = 0
            for i, day in enumerate(day_array):
                remaining = day_remain_dict.get(day, Decimal('0'))
                dictionary['data'].append({'x': f'day {i}', 'y': float(round(remaining, 2))})

        result.append(dictionary)

    return Response({'result': result})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def pie_chart(request):
    iteration = request.query_params.get('iteration')
    story_queryset = Story.objects.filter(iteration=iteration).filter(is_active=True)
    incomplete_story = story_queryset.filter(is_complete=False).count()
    complete_story = story_queryset.filter(is_complete=True).count()

    incomplete_dict = dict(id="incomplete story", label="incomplete", value=incomplete_story)
    complete_dict = dict(id="complete story", label="complete", value=complete_story)
    result = [incomplete_dict, complete_dict]
    print(result)

    return Response({'result': result})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def pie_chart_projects(request):
    iteration = request.query_params.get('iteration')
    story_queryset = Story.objects.filter(iteration=iteration).filter(is_active=True)
    story_count = story_queryset.count()

    project_counts = []

    for story in story_queryset:
        project_id = story.project.id
        project_name = story.project.name

        # Check if a dictionary with the same 'id' already exists in the list
        existing_project = next((project for project in project_counts if project['id'] == project_id), None)

        if existing_project:
            existing_project['value'] += 1
        else:
            project_counts.append({
                'id': project_id,
                'name': project_name,
                'value': 1  # Initialize the count to 1
            })

    for project in project_counts:
        project['id'] = project['name']

    return Response({'result': project_counts})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def iteration_total_efforts(request):
    iteration = request.query_params.get('iteration')

    task_queryset = Task.objects.filter(iteration=iteration, is_active=True)
    total_tasks = task_queryset.count()
    total_estimate_time = task_queryset.aggregate(Sum('estimate_time'))['estimate_time__sum'] or 0

    result_dict = {
        'total_tasks': total_tasks,
        'total_estimate_hours': total_estimate_time,
    }

    return Response({'result': result_dict})



@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_incomplete_story(request):

    user = request.user
    team_id = request.query_params.get('team')
    # iteration = request.query_params.get('iteration')
    team = get_object_or_404(Team, pk=int(team_id))
    iteration = Iteration.objects.filter(team=team).filter(is_active=True).first()

    task_queryset = Task.objects.filter(user=user).filter(iteration=iteration).filter(is_active=True).exclude(status="complete")

    story_ids = list(task_queryset.values_list('story', flat=True))
    story_queryset = Story.objects.filter(id__in=story_ids).filter(is_active=True)
    serialized_story = StorySerializer(story_queryset, many=True)

    return Response({'result': serialized_story.data})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def effort_hour_by_user(request):
    team_id = request.query_params.get('team')
    # iteration = request.query_params.get('iteration')
    team = get_object_or_404(Team, pk=int(team_id))
    iteration = Iteration.objects.filter(team=team).filter(is_active=True).first()

    task_queryset = Task.objects.filter(iteration=iteration).filter(is_active=True)

    # completed task effort
    complete_task_queryset = task_queryset.filter(status=Task.STATUS_COMPLETE)
    effort_group_by = list(complete_task_queryset.values(fullname=F('user__fullname'))
                           .annotate(effort=Sum('estimate_time'))
                           .order_by())

    # taken task but incomplete
    taken_task_queryset = task_queryset.exclude(status=Task.STATUS_COMPLETE)
    taken_group_by = list(taken_task_queryset.values(fullname=F('user__fullname'))
                          .annotate(assign=Sum('estimate_time'))
                          .order_by())

    total_dict  =   defaultdict(dict)

    for item in taken_group_by + effort_group_by:
        total_dict[item['fullname']].update(item)
        total_dict[item['fullname']].setdefault('assign', 0)
        total_dict[item['fullname']].setdefault('effort', 0)

    total_list  = list(total_dict.values())
    
    # actual hour added
    actual_group_by = [
        {
            'fullname': user_effort['fullname'],
            'actual': user_effort.get('effort') + user_effort.get('assign')
        }
            for user_effort in total_list
    ]

    result_dict = defaultdict(dict)
    for item in effort_group_by + taken_group_by + actual_group_by:
        if item['fullname'] is not None:  # Filter out None values
            result_dict[item['fullname']].update(item)

    result = list(result_dict.values())

    return Response({'result': result})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_capacity_by_iteration(request):
    team_id = request.query_params.get('team')
    # iteration_id = request.query_params.get('iteration')
    # iteration = get_object_or_404(Iteration, pk=int(iteration_id))
    team = get_object_or_404(Team, pk=int(team_id))
    iteration = Iteration.objects.filter(team=team).filter(is_active=True).first()

    event_calendar_qs = EventCalendar.objects.filter(is_active=True).filter(start_date__gte=iteration.start_date) \
                                             .filter(end_date__lte=iteration.end_date)

    user_leave_list = list(event_calendar_qs.values(fullname=F('user__fullname'))
                           .annotate(total_days=Sum('total_days'))
                           .order_by())
    
    team_member_qs = TeamMember.objects.filter(team=iteration.team).filter(is_active=True)

    # look for holiday for everyone
    total_holiday = 0
    for holiday in user_leave_list:
        if holiday['fullname'] == None:
            total_holiday = holiday['total_days']
            break

    result = []
    for team_member in team_member_qs:
        dictionary = {}

        # total_leave should add up with holiday
        total_leave = total_holiday
        for leave in user_leave_list:
            if leave['fullname'] == team_member.user.fullname:
                total_leave += leave['total_days']
                break

        capacity = team_member.user.capacity
        actual_capacity = float(capacity) / 5 * (5 - float(total_leave))

        # Round to two decimal points
        actual_capacity = round(actual_capacity, 2)

        dictionary['fullname'] = team_member.user.fullname
        dictionary['capacity'] = actual_capacity
        result.append(dictionary)
    
    return Response({'result': result})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_monthly_effort(request):

    iteration_id = request.query_params.get('iteration')
    iteration = get_object_or_404(Iteration, pk=int(iteration_id))

    task_queryset = Task.objects.filter(iteration=iteration).filter(is_active=True)

    # completed task effort
    complete_task_queryset = task_queryset.filter(status=Task.STATUS_COMPLETE)

    # get total effort
    total_effort_count = complete_task_queryset.aggregate(Sum('estimate_time'))

    effort_list = list(complete_task_queryset.values(fullname=F('user__fullname'))
                       .annotate(effort=Sum('estimate_time'))
                       .order_by())

    event_calendar_qs = EventCalendar.objects.filter(is_active=True).filter(start_date__gte=iteration.start_date) \
                                             .filter(end_date__lte=iteration.end_date)

    user_leave_list = list(event_calendar_qs.values(fullname=F('user__fullname'))
                           .annotate(total_days=Sum('total_days'))
                           .order_by())

    team_member_qs = TeamMember.objects.filter(team=iteration.team).filter(is_active=True)

    # look for holiday for everyone
    total_holiday = 0
    for holiday in user_leave_list:
        if holiday['fullname'] == None:
            total_holiday = holiday['total_days']
            break

    result = []
    total_capacity = 0
    for team_member in team_member_qs:
        user_fullname = team_member.user.fullname
        dictionary = {}

        # total_leave should add up with holiday
        total_leave = total_holiday
        total_effort = 0
        for leave in user_leave_list:
            if leave['fullname'] == user_fullname:
                total_leave += leave['total_days']
                break

        for effort in effort_list:
            if effort['fullname'] == user_fullname:
                total_effort = effort['effort']

        capacity = team_member.user.capacity
        actual_capacity = float(capacity) / 5 * (5 - float(total_leave))

        # Round to two decimal points
        actual_capacity = round(actual_capacity, 2)

        dictionary['fullname'] = user_fullname
        dictionary['capacity'] = actual_capacity
        dictionary['effort'] = total_effort

        result.append(dictionary)

        # sum up everyone capacity
        total_capacity += actual_capacity

        # Round to two decimal points
        total_capacity = round(total_capacity, 2)

    overall_dict = {}
    overall_dict['effort'] = total_effort_count['estimate_time__sum']
    overall_dict['capacity'] = total_capacity

    return Response({'result': {'data': result, 'overall': overall_dict}})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def bugs_count_pie_chart(request):
    team_id = request.query_params.get('team')
    iteration_ids_param = request.query_params.get('iteration')
    project_id = request.query_params.get('project', 0)
    project_id = int(project_id)

    if not team_id:
        return Response({'Error: No team id pass in'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if not iteration_ids_param:
        latest_iteration = Iteration.objects.filter(team=team_id, is_active=True).order_by('id').last()
        iteration_ids = [latest_iteration.id]
    else:
        iteration_ids = [int(id) for id in iteration_ids_param.split(',')]

    team_members = TeamMember.objects.filter(team_id=team_id).filter(is_active=True).values('user')

    user_ids = [team_member['user'] for team_member in team_members]

    all_user_ids = set(user_ids)

    task_queryset = Task.objects.filter(
                user__id__in=user_ids,
                iteration__id__in=iteration_ids, 
                is_bug=True,
                is_active=True
            )
    
    if project_id :
        task_queryset = task_queryset.filter(story__project_id=project_id)

    bug_count_by_user = task_queryset.values('user__fullname', 'user__id').annotate(bug_count=Count('id'))

    bug_counts = {user_bug['user__id']: user_bug['bug_count'] for user_bug in bug_count_by_user}

    total_bug_count = sum(bug_counts.values())
    user_bugs = []

    for user_id in all_user_ids:
        user_fullname = User.objects.get(id=user_id).fullname  
        user_bugs.append({
            'id': user_fullname,  
            'label': user_fullname, 
            'value': bug_counts.get(user_id, 0),  
        })

    return Response({'result': user_bugs, 'total_bugs':total_bug_count})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def first_user_achieve_effort(request):
    team_id = request.query_params.get('team')
    #team = get_object_or_404(Team, pk=int(team_id))
    iteration_id = request.query_params.get('iteration')
    iteration = get_object_or_404(Iteration, pk=int(iteration_id))

    task_queryset = Task.objects.filter(iteration=iteration, is_active=True, status=Task.STATUS_COMPLETE).order_by('status_complete_at')

    result_dict = defaultdict(lambda: {'total_effort': 0, 'latest_status_complete_at': None})

    # Iterate through tasks to accumulate effort and update latest status_complete_at
    for item in task_queryset:
        user_fullname = item.user
        estimate_time = item.estimate_time
        status_complete_at = item.status_complete_at

        # Check if the previous total_effort is not greater than 30
        if result_dict[user_fullname]['total_effort'] < 30:
            result_dict[user_fullname]['total_effort'] += estimate_time

            result_dict[user_fullname]['latest_status_complete_at'] = status_complete_at
        else: 
            result_dict[user_fullname]['total_effort'] += estimate_time

    result_list = [
        {
            'fullname': str(user),
            'total_effort': info['total_effort'],
            'rocket_at': info['latest_status_complete_at']
        }
        for user, info in result_dict.items()
    ]

    sorted_result = sorted(result_list, key=lambda x: (-x["total_effort"], x["rocket_at"]))    
    
    return Response({'result': sorted_result})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def project_story_reporting(request):
    iteration_id = request.query_params.get('iteration')
    team_id = request.query_params.get('team')
    
    if not iteration_id:
        return Response({'error': 'Iteration ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    story_queryset = Story.objects.filter(
        iteration_id=iteration_id,
        is_active=True
    )
    
    if team_id:
        story_queryset = story_queryset.filter(team_id=team_id)
    
    project_data = story_queryset.values(
        'project_id',
        'project__name'
    ).annotate(
        total_story=Count('id'),
        total_estimated_hour=Sum('total_estimate_time')
    ).order_by('-total_estimated_hour')
    
    total_stories = sum(item['total_story'] for item in project_data)
    total_hours = sum(item['total_estimated_hour'] or 0 for item in project_data)
    
    data = []
    for item in project_data:
        estimated_hour = item['total_estimated_hour'] or 0
        percentage = (estimated_hour / total_hours * 100) if total_hours > 0 else 0
        
        data.append({
            'project_id': item['project_id'],
            'project_name': item['project__name'],
            'total_story': item['total_story'],
            'total_estimated_hour': float(estimated_hour),
            'percentage': round(percentage, 2)
        })
    
    result = {
        'data': data,
        'total': {
            'total_story': total_stories,
            'total_estimated_hour': float(total_hours),
            'percentage': 100.0
        }
    }
    
    return Response({'result': result})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def season_summary(request):
    """
    Summary for the given season (date range)
    """

    # ?start=2025-11-23&end=2025-12-06&teamId=12
    # ?start= & end= (format is YYYY-MM-DD e.g. 2025-01-01)
    start_date = request.query_params.get("start")
    end_date = request.query_params.get("end")
    team_id = request.query_params.get("teamId")
    # user_id = request.query_params.get("userId")

    if not start_date and not end_date:
        return Response({"error": "start and end date required"}, status=status.HTTP_400_BAD_REQUEST)
    
    if not team_id:
        return Response({"error": "team id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    # if not user_id:
    #    return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Filter iterations inside the season perioad
    iterations = Iteration.objects.filter(
        start_date__gte = start_date,
        end_date__lte = end_date,
        team_id = team_id,
        is_active = True
    )

    # Filter stories inside those iterations
    stories = Story.objects.filter(
        iteration__in = iterations,
        team_id = team_id,
        is_active = True
    )

    # Filter tasks for those stories
    tasks = Task.objects.filter(
        story__in = stories,
        status=Task.STATUS_COMPLETE,
        # user_id = user_id,
        is_active = True
    )

    # Top 3 contributed (sum of hours)
    top_project = (
        tasks.values(
            project_id = F("story__project__id"),
            project_name = F("story__project__name"),
        )
        .annotate(total_hours=Sum("total_hour_used"))
        .order_by("-total_hours")[:3]
    )

    # Total task done by users
    total_tasks_by_users = (
        tasks.values(
            "user_id",
            fullname = F("user__fullname")
        )
        .annotate(total_tasks=Count("id"))
        .order_by("-total_tasks")
    )

    # Total hour commmitted by users
    total_hours_committed_by_user = (
        tasks.values(
            "user_id",
            fullname = F("user__fullname")
        )
        .annotate(total_hour=Sum("total_hour_used"))
        .order_by("-total_hour")
    )

    # Total solo task done by users
    total_solo_by_users = (
        tasks.values(
            "user_id",
            fullname = F("user__fullname")
        )
        .filter(story__is_multi=False)
        .annotate(total_solo=Count("id"))
        .order_by("-total_solo")
    )

    # Total rnd taskd done by users
    total_rnd_by_users = (
        tasks.values(
            "user_id",
            fullname = F("user__fullname")
        )
        .filter(story__is_rnd=True)
        .annotate(total_rnd=Count("id"))
        .order_by("-total_rnd")
    )

    # Total task verified by users
    total_verified_by_users = (
        VerifiedByUser.objects.values(
            "user_id",
            fullname = F("user__fullname")
        )
        .filter(story__in=stories)
        .annotate(total_verified=Count("id"))
        .order_by("-total_verified")
    )

    # Total task bug created by users
    total_bug_by_users = (
        tasks.values(
            "user_id",
            fullname = F("user__fullname")
        )
        .filter(is_bug=True)
        .annotate(total_bug=Count("id"))
        .order_by("-total_bug")
    )


    # Build result
    result = {
        "top_projects": top_project,
        "total_tasks_by_users": total_tasks_by_users,
        "total_hours_committed_by_user": total_hours_committed_by_user,
        "total_solo_by_users": total_solo_by_users,
        "total_rnd_by_users": total_rnd_by_users,
        "total_verified_by_users": total_verified_by_users,
        "total_bug_by_users": total_bug_by_users,
    }

    return Response({"result": result})


from django.db.models import Avg, Sum
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions, status
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404

# Import your models
# from .models import Iteration, Task, TaskHour

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def burndown_chart(request):
    DAYS_COUNT = 7
    iteration_id = request.query_params.get('iteration')

    if not iteration_id:
         return Response({"error": "Missing ID"}, status=status.HTTP_400_BAD_REQUEST)

    # 1. Get Current Iteration
    iteration_obj = Iteration.objects.filter(id=iteration_id, is_active=True).first()
    if iteration_obj is None:
        return Response({"detail": "Iteration not found."}, status=status.HTTP_404_NOT_FOUND)
    
    start_date = iteration_obj.start_date
    all_days = [start_date + timedelta(days=x) for x in range(DAYS_COUNT)]
    working_days = [d for d in all_days if d.weekday() < 5] # Mon-Fri (5 days)
    total_working_days = len(working_days)

    today = timezone.localdate() # Best practice for Django

    # Future setup
    future_days_list = [d for d in working_days if d > today]
    total_future_days_count = len(future_days_list)
    last_actual_points = 0

    tasks = Task.objects.filter(iteration_id=iteration_id, is_active=True)

    # ====================================================
    # CALCULATE IDEAL START POINTS
    # ====================================================
    # Check for all user capacity

    ideal_start_points = TeamMember.objects.filter(
        team=iteration_obj.team
    ).aggregate(total=Sum('user__capacity'))['total'] or 0

    # Calculate Drop Rate (Burn Rate) for Ideal Line
    ideal_burn_rate = ideal_start_points / total_working_days

    # ====================================================
    # STEP 1: CALCULATE Day 0 (Start)
    # ====================================================
    d0_total_actual = sum(
        float(t.estimate_time or 0) 
        for t in tasks 
        if t.create_at.date() <= start_date
    )

    result = []
    result.append({
        "day": "Day 0",
        "total_points": round(d0_total_actual, 2),
        "ideal_points": round(ideal_start_points, 2),
        "type": "actual"
    })
    
    last_actual_points = d0_total_actual


    # ====================================================
    # STEP 2: LOOP THROUGH DAYS
    # ====================================================
    for index, current_day in enumerate(working_days):
        daily_total_points = 0
        
        # --- 1. CALCULATE ACTUAL POINTS ---
        if current_day <= today:
            for task in tasks:
                # If the task is created in the future relative to 'current_day', skip it.
                if task.create_at.date() > current_day:
                    continue 

                estimate = float(task.estimate_time or 0)

                # Get logs UP TO today (Cumulative), not just equal to today
                logs_until_today = TaskHour.objects.filter(
                    task=task,
                    create_at__date__lte=current_day,
                    is_active=True 
                ).order_by('create_at')

                # Case A: Task exists, but no work logged yet. 
                if not logs_until_today.exists():
                    daily_total_points += estimate
                    continue

                # Case B: Calculate using Formula
                logs_list = list(logs_until_today)
                
                spent = sum(float(log.hour or 0) for log in logs_list)
                
                latest_log = logs_list[-1]
                remaining = float(latest_log.remain_hour or 0)
                
                denominator = spent + remaining

                if denominator == 0:
                    point = 0
                else:
                    point = (remaining / denominator) * estimate
                
                daily_total_points += point
            
            last_actual_points = daily_total_points

        # --- 2. CALCULATE PROJECTED POINTS ---
        else:
            if total_future_days_count > 0:
                burn_rate_per_day = last_actual_points / total_future_days_count
                future_step_index = future_days_list.index(current_day) + 1
                projected_points = last_actual_points - (burn_rate_per_day * future_step_index)
                daily_total_points = max(0, projected_points)
            else:
                daily_total_points = 0

        # --- 3. CALCULATE IDEAL POINTS (Linear Drop) ---
        current_ideal = ideal_start_points - (ideal_burn_rate * (index + 1))
        
        result.append({
            "day": f"Day {index + 1}",
            "total_points": round(daily_total_points, 2),
            "ideal_points": round(max(0, current_ideal), 2),
            "type": "actual" if current_day <= today else "projected"
        })

    return Response({
        "result": result
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def capacity_reporting(request):
    DAY_PER_WEEK = 5

    user = request.user
    team_id = request.query_params.get('team_id')
    period = request.query_params.get('period', 'daily')
    iteration = request.query_params.get('iteration')
    
    if not team_id:
        return Response({"error": "Missing team ID"}, status=status.HTTP_400_BAD_REQUEST)

    if not period:
        return Response({"error": "Missing period (daily or weekly)"}, status=status.HTTP_400_BAD_REQUEST)

    if iteration and period == 'weekly':
        iteration = get_object_or_404(Iteration, pk=int(iteration))
    else:
        iteration = Iteration.objects.filter(team=team_id, is_active=True).order_by("-start_date").first()
    
    filters = {'iteration': iteration, 'is_active': True}
    
    if period == 'daily':
        today = datetime.now().date()
        filters['assigned_at__date'] = today
        capacity = user.capacity / DAY_PER_WEEK
    else:
        capacity = user.capacity

    tasks = user.task_set.filter(**filters)

    total_capacity = tasks.filter(status=Task.STATUS_COMPLETE).aggregate(Sum('estimate_time'))['estimate_time__sum'] or 0
    total_estimate = tasks.aggregate(Sum('estimate_time'))['estimate_time__sum'] or 0
    total_committed = tasks.aggregate(Sum('total_hour_used'))['total_hour_used__sum'] or 0

    project_estimates = tasks.values(
        project_name=F('story__project__name')
    ).annotate(
        total_estimate_per_project=Sum('estimate_time')
    ).order_by('-total_estimate_per_project')

    tasks_data = tasks.values(
        'id', 
        'description', 
        'status', 
        'estimate_time', 
        'total_hour_used',
        'story',
        story_name=F('story__name'),
    ).order_by('assigned_at')

    return Response({
        "iteration": iteration.id,
        "period": period,
        "capacity": capacity,
        "total_capacity": total_capacity,
        "total_estimate": total_estimate,
        "total_committed": total_committed,
        "project_estimates": list(project_estimates),
        "tasks": list(tasks_data)
    })