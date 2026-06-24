from dynamic_rest.serializers import DynamicModelSerializer
from dynamic_rest.serializers import DynamicModelSerializer
from core.serializers import UserSerializer
from .models import Team, TeamMember
from dynamic_rest.fields.fields import DynamicRelationField
from rest_framework import serializers 

from core.serializers import UserSerializer
from .models import Team, TeamMember
from dynamic_rest.fields.fields import DynamicRelationField

class TeamSerializer(DynamicModelSerializer):
    # Define a custom image field
    team_image = serializers.ImageField(required=False)  # Replace 'image' with the actual field name

    class Meta:
        model = Team
        name = 'team'
        fields = ('id', 'name', 'is_active', 'create_at', 'update_at', 'team_image')  # Include 'team_image' in the fields
        read_only_fields = ('id',)

class TeamMemberSerializer(DynamicModelSerializer):
    user = DynamicRelationField(UserSerializer)
    team = DynamicRelationField(TeamSerializer)

    class Meta:
        model = TeamMember
        name = 'team-member'
        fields = ('id', 'team', 'user', 'is_active', 'hashid')
        read_only_fields = ('id',)

