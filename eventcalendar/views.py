from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from core.views import BaseDynamicModelViewSet
from eventcalendar.models import EventCalendar
from eventcalendar.serializers import EventCalendarSerializer

# Create your views here.
class EventCalendarViewSet(BaseDynamicModelViewSet):
    serializer_class = EventCalendarSerializer
    queryset = EventCalendar.objects.all()
    http_method_names = ['get','post', 'put', 'patch','delete']

    @action(methods=['get'], url_path='event-calendar-by-range', detail=False)
    def event_calendar_by_range(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            return Response("Must provide start_date and end_date", status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset().filter(
            start_date__gte=start_date, 
            end_date__lte=end_date
        )

        queryset = self.filter_queryset(queryset)
        serializer = self.get_serializer(queryset, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)