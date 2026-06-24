from dynamic_rest.serializers import DynamicModelSerializer
from dynamic_rest.fields.fields import DynamicRelationField
from dynamic_rest.fields import DynamicMethodField
from core.serializers import UserSerializer
from iteration.serializers import IterationSerializer
from project.serializers import ProjectSerializer
from team.serializers import TeamSerializer
from .models import Tag, Story, StoryImage, VerifiedByUser, TagItem
from task.models import Task, TaskHour
from django.db.models import Sum, Count

class TagSerializer(DynamicModelSerializer):
    project = DynamicRelationField(ProjectSerializer)
    team = DynamicRelationField(TeamSerializer)

    class Meta:
        model = Tag
        name = 'tag'
        fields = ['id', 'name', 'color', 'project', 'team']
        read_only_fields = ['id', 'create_by', 'update_by']

class StorySerializer(DynamicModelSerializer):
    iteration = DynamicRelationField(IterationSerializer)
    project = DynamicRelationField(ProjectSerializer)
    team = DynamicRelationField(TeamSerializer)
    parent_story = DynamicRelationField('StorySerializer')
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Story
        name = 'story'
        fields = ('name', 'id', 'description', 'short_description', 'iteration', 'project', 'team', 'priority', 
                  'is_complete', 'is_delivered', 'is_require_tester', 'parent_story', 'is_pendingReview', 
                  'status', 'is_rnd', 'need_verify', 'verify_at', 'is_multi', 'total_estimate_time', 
                  'is_needed_to_deploy', 'deployment_status', 'deployment_staging_status_at', 
                  'deployment_production_status_at', 'has_issue', 'issue_resolved_at',
                  'create_at', 'update_at', 'create_by', 'update_by','completed_at', 'tags')
        read_only_fields = ['id', 'is_complete', 'total_estimate_time', 'verify_at', 
                           'create_at', 'update_at', 'create_by', 'update_by', 'completed_at']
class StoryImageSerializer(DynamicModelSerializer):
    story = DynamicRelationField(StorySerializer)
    class Meta:
        model = StoryImage
        name = 'story-image'
        fields = ('id', 'story', 'image', 'update_at')
        read_only_fields = ['id']
        
class StoryProjectSerializer(DynamicModelSerializer):
    project = ProjectSerializer()

    class Meta:
        model = Story
        name = 'story-project'
        fields = ('name', 'id', 'description', 'short_description', 'project', 'priority',
                 'is_needed_to_deploy', 'deployment_status', 'has_issue')
        read_only_fields = ('name', 'id', 'description', 'short_description', 'project', 'priority',
                           'is_needed_to_deploy', 'deployment_status', 'has_issue') 
class VerifiedByUserSerializer(DynamicModelSerializer):
    story = DynamicRelationField(StorySerializer)
    iteration = DynamicRelationField(IterationSerializer)
    user = DynamicRelationField(UserSerializer)

    class Meta:
        model = VerifiedByUser
        name = 'verified-by-user'
        fields = ('id', 'story', 'iteration', 'user', 'total_hour_used', 'is_active')
        read_only_fields = ['id']

class TagItemSerializer(DynamicModelSerializer):
    tag = DynamicRelationField(TagSerializer)
    story = DynamicRelationField(StorySerializer)

    class Meta:
        model = TagItem
        name = 'tag-item'
        fields = ('id', 'tag', 'story')
        read_only_fields = ['id']