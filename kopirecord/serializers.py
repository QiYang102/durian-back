from dynamic_rest.serializers import DynamicModelSerializer
from dynamic_rest.fields.fields import DynamicRelationField
from core.serializers import UserSerializer
from iteration.serializers import IterationSerializer
from .models import KopiRecord

class KopiRecordSerializer(DynamicModelSerializer) :
    member_name = DynamicRelationField(UserSerializer)
    iteration = DynamicRelationField(IterationSerializer)

    class Meta:
        model = KopiRecord
        name = 'kopibeng'
        fields = ('id', 'create_date','member_name','iteration','remark','amount','status','complete_date')
        read_only_fields = ('id',)

