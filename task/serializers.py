from dynamic_rest.serializers import DynamicModelSerializer
from dynamic_rest.fields.fields import DynamicRelationField
from iteration.serializers import IterationSerializer
from core.serializers import UserSerializer
from story.serializers import StorySerializer
from .models import Task, TaskHour, TaskImage, TaskTemplate, TaskTemplateItem
from dynamic_rest.fields import DynamicMethodField

class TaskSerializer(DynamicModelSerializer):
    iteration = DynamicRelationField(IterationSerializer)
    story = DynamicRelationField(StorySerializer)
    user = DynamicRelationField(UserSerializer)

    class Meta:
        model = Task
        name = 'task'
        fields = ('id','description','is_bug','due_date', 'estimate_time', 'total_hour_used', 'status', 'iteration', 
                  'story', 'user','is_active', 'status_complete_at','create_at', 'update_at', 'assigned_at')
        read_only_fields = ['id', 'total_hour_used', 'create_at', 'update_at', 'assigned_at']
    
class TaskHourSerializer(DynamicModelSerializer):
    user = DynamicRelationField(UserSerializer)
    task = DynamicRelationField(TaskSerializer)
    total_remain_hour = DynamicMethodField()
    class Meta:
        model = TaskHour
        name = 'task-hour'
        fields = ('id', 'hour', 'remain_hour', 'status', 'user', 'task', 'update_at', 'total_remain_hour', 'is_active', 'create_at')
        read_only_fields = ['id', 'total_remain_hour']

    def get_total_remain_hour(self, obj):
        # Filter TaskHour instances related to the task
        task_hours = TaskHour.objects.filter(task=obj.task).filter(is_active=True)
        
        # Calculate the total remaining hour
        total_remain_hour = sum(task_hour.remain_hour for task_hour in task_hours)
        
        return total_remain_hour
    
class TaskImageSerializer(DynamicModelSerializer):
    task = DynamicRelationField(TaskSerializer)
    class Meta:
        model = TaskImage
        name = 'task-image'
        fields = ('id', 'task', 'image', 'update_at')
        read_only_fields = ['id']

class TaskTemplateSerializer(DynamicModelSerializer):
    class Meta:
        model = TaskTemplate
        name = 'task-template'
        fields = ('id','name')
        read_only_fields = ['id']

class TaskTemplateItemSerializer(DynamicModelSerializer):
    template = DynamicRelationField(TaskTemplateSerializer)

    class Meta:
        model = TaskTemplateItem
        name = 'task-template-item'
        fields = ('id', 'description','task_template')
        read_only_fields = ['id']