from dynamic_rest.serializers import DynamicModelSerializer
from dynamic_rest.fields.fields import DynamicRelationField
from team.serializers import TeamSerializer
from .models import Project

class ProjectSerializer(DynamicModelSerializer):
    team = DynamicRelationField(TeamSerializer)
    
    class Meta:
        model = Project
        name = 'project'
        fields = ('id','team','name')
