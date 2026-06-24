from dynamic_rest.serializers import DynamicModelSerializer
from dynamic_rest.fields.fields import DynamicRelationField
from core.serializers import UserSerializer
from .models import EventCalendar


class EventCalendarSerializer(DynamicModelSerializer):
    user = DynamicRelationField(UserSerializer)

    class Meta:
        model = EventCalendar
        name = 'event_calendar'
        fields = ('id', 'type', 'start_date', 'end_date', 'description', 'user', 'name', 'total_days')
        read_only_fields = ('id',)
