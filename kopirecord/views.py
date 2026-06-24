from django.shortcuts import render
from core.views import BaseDynamicModelViewSet
from kopirecord.models import KopiRecord
from kopirecord.serializers import KopiRecordSerializer

from django.db.models import Sum,F
from rest_framework.decorators import action
from rest_framework.response import Response

# Create your views here.
class KopiRecordViewSet(BaseDynamicModelViewSet):
    serializer_class = KopiRecordSerializer
    queryset = KopiRecord.objects.all()
    http_method_names = ['get','post', 'put', 'patch','delete']

    @action(methods=['get'], url_path='user-overall-kopi', detail=False)
    def user_overall_kopi(request, self):
        kopiRecord_qs = KopiRecord.objects.filter(status='owing')
        user_kopi_list = list(kopiRecord_qs.values(fullname=F('member_name__fullname'), userId=F('member_name__id'))
                            .annotate(amount=Sum('amount'))
                            .order_by())
        result = []
        return Response({'result': user_kopi_list})


    @action(methods=['get'], url_path='top3-user-kopibeng', detail=False)
    def user_overall_kopi(self, request):
        base = request.build_absolute_uri('/')[:-1]

        data = list(
            KopiRecord.objects
            .values(
                fullname=F('member_name__fullname'),
                userId=F('member_name__id'),
                image=F('member_name__image'),
            )
            .annotate(amount=Sum('amount'))
            .order_by('-amount')[:3]
        )

        for item in data:
            if item["image"]:
                item["image"] = f"{base}/media/{item['image']}"

        return Response({"result": data})