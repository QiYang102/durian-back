from dynamic_rest.serializers import DynamicModelSerializer
from dynamic_rest.fields.fields import DynamicRelationField
from rest_framework import serializers

from core.serializers import UserSerializer
from .models import Announcement


class AnnouncementSerializer(DynamicModelSerializer):
    created_by = DynamicRelationField(UserSerializer, read_only=True)

    class Meta:
        model = Announcement
        name = 'announcement'
        fields = (
            'id', 
            'name',  
            'created_by', 
            'start_date', 
            'end_date', 
            'description', 
            'is_live',
            'is_active', 
            'create_at', 
            'update_at',
            'hashid'
        )
        read_only_fields = ('id', 'created_by', 'hashid')