from dynamic_rest.serializers import DynamicModelSerializer
from dynamic_rest.fields.fields import DynamicRelationField
from team.serializers import TeamSerializer
from .models import Season

class SeasonSerializer(DynamicModelSerializer) :
    team = DynamicRelationField(TeamSerializer)

    class Meta:
        model = Season
        name = 'season'
        fields = ('id', 'season_name', 'start_date', 'end_date', 'team', 'report_data')
        read_only_fields = ('id',)
