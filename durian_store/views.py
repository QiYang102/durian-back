from rest_framework.permissions import AllowAny, IsAuthenticated
from dynamic_rest.viewsets import DynamicModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Category, Product, PromoCode, Order
from .serializers import CategorySerializer, ProductSerializer, PromoCodeSerializer, OrderSerializer

class CategoryViewSet(DynamicModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    http_method_names = ['get']

class ProductViewSet(DynamicModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get']

class PromoCodeViewSet(DynamicModelViewSet):
    queryset = PromoCode.objects.all()
    serializer_class = PromoCodeSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def validate(self, request):
        code = request.data.get('code')
        try:
            promo = PromoCode.objects.get(name=code)
            return Response(self.get_serializer(promo).data)
        except PromoCode.DoesNotExist:
            return Response({'error': 'Invalid code'}, status=400)

class OrderViewSet(DynamicModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Order.objects.filter(user=self.request.user)
        if self.action in ['retrieve', 'upload_receipt']:
            return Order.objects.all()
        return Order.objects.none()

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()

    @action(detail=True, methods=['post'])
    def upload_receipt(self, request, pk=None):
        try:
            order = Order.objects.get(hashid=pk)
        except Order.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
            
        receipt = request.FILES.get('receipt')
        if receipt:
            order.payment_receipt = receipt
            order.status = 'paid'
            order.save()
            return Response({'status': 'receipt uploaded'})
        return Response({'error': 'No receipt provided'}, status=400)
