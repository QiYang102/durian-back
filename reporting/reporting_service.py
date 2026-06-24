from django.db.models import Sum
from task.models import Task, TaskHour
from core.models import User

def get_user_task_statistics(iteration_id=None, team_id=None, user_id=None):
    """
    Calculate task statistics per user including:
    - Multi task count
    - Solo task count
    - Priority task count
    - R&D task count
    - Total tasks completed
    - Total hours committed
    
    Returns a list of dictionaries with user stats
    """
    tasks_qs = Task.objects.select_related('user', 'story', 'iteration')
    
    if iteration_id:
        tasks_qs = tasks_qs.filter(iteration_id=iteration_id)
    
    if team_id:
        tasks_qs = tasks_qs.filter(iteration__team_id=team_id)

    if user_id:
        users_with_tasks = User.objects.filter(id=user_id)
    else:
        users_with_tasks = User.objects.filter(task__isnull=False).distinct()
        
    stats = []
    
    for user in users_with_tasks:
        user_tasks = tasks_qs.filter(user=user)
        
        multi_task_count = user_tasks.filter(story__is_multi=True).count()
        solo_task_count = user_tasks.filter(story__is_multi=False).count()
        priority_task_count = user_tasks.filter(story__priority='high').count()
        rnd_task_count = user_tasks.filter(story__is_rnd=True).count()
        completed_task_count = user_tasks.filter(status=Task.STATUS_COMPLETE).count()
        
        total_hours_committed = TaskHour.objects.filter(
            user=user,
            task__in=user_tasks
        ).aggregate(total=Sum('hour'))['total'] or 0
        
        stats.append({
            'user_id': user.id,
            'user_name': user.fullname,
            'user_email': user.email,
            'multi_task_count': multi_task_count,
            'solo_task_count': solo_task_count,
            'priority_task_count': priority_task_count,
            'rnd_task_count': rnd_task_count,
            'completed_task_count': completed_task_count,
            'total_hours_committed': float(total_hours_committed),
            'total_task_count': user_tasks.count()
        })
    
    return stats