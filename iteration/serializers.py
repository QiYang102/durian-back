from dynamic_rest.serializers import DynamicModelSerializer
from dynamic_rest.fields.fields import DynamicRelationField
from dynamic_rest.fields import DynamicMethodField
from team.serializers import TeamSerializer
from .models import Iteration

class IterationSerializer(DynamicModelSerializer):
    team = DynamicRelationField(TeamSerializer)
    total_story  = DynamicMethodField()
    total_bugs  = DynamicMethodField()
    total_tasks  = DynamicMethodField()
    
    class Meta:
        model = Iteration
        name = 'iteration'
        fields = ('id', 'name', 'start_date', 'end_date', 'status', 'team','total_story', 'total_bugs', 'total_tasks')
        read_only_fields = ['id','total_story', 'total_bugs', 'total_tasks']

    def get_total_story(self,obj):
        return obj.story_set.all().filter(is_active=True).count()
    
    def get_total_bugs(self, obj):
        total_used_time = 0
        total_bugs = obj.task_set.filter(is_bug=True).filter(is_active=True).count()
        for task in obj.task_set.filter(is_bug=True).filter(is_active=True):
            total_used_time += task.total_hour_used
        return [total_bugs, total_used_time]
    
    def get_total_tasks(self, obj):
        total_used_time = 0
        total_tasks = obj.task_set.filter(is_bug=False).filter(is_active=True).count()
        for task in obj.task_set.filter(is_bug=False).filter(is_active=True):
            total_used_time += task.total_hour_used
        return [total_tasks, total_used_time]