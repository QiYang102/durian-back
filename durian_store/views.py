from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser, BasePermission
from dynamic_rest.viewsets import DynamicModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count
from django.utils import timezone
from .models import Category, Product, PromoCode, Order, SystemSetting, HomeBanner
from .serializers import CategorySerializer, ProductSerializer, PromoCodeSerializer, OrderSerializer, SystemSettingSerializer, HomeBannerSerializer

class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (getattr(request.user, 'role', None) == 'admin' or request.user.is_staff or request.user.is_superuser))

class CategoryViewSet(DynamicModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    http_method_names = ['get']

class ProductViewSet(DynamicModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_permissions(self):
        if self.action == 'upload_image':
            return [IsAdminRole()]
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [IsAdminRole()]
        return [AllowAny()]

    @action(detail=True, methods=['post'])
    def upload_image(self, request, pk=None):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
            
        image = request.FILES.get('image')
        if image:
            product.image = image
            product.save()
            image_url = request.build_absolute_uri(product.image.url)
            return Response({'status': 'image uploaded', 'image_url': image_url})
        return Response({'error': 'No image file provided'}, status=400)

class PromoCodeViewSet(DynamicModelViewSet):
    queryset = PromoCode.objects.all()
    serializer_class = PromoCodeSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_permissions(self):
        if self.action == 'validate':
            return [AllowAny()]
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [IsAdminRole()]
        return [AllowAny()]

    @action(detail=False, methods=['post'])
    def validate(self, request):
        code = request.data.get('code')
        try:
            promo = PromoCode.objects.get(name=code)
            if promo.current_uses >= promo.max_uses:
                return Response({'error': 'Promo code usage limit reached'}, status=400)
                
            return Response(self.get_serializer(promo).data)
        except PromoCode.DoesNotExist:
            return Response({'error': 'Invalid code'}, status=400)

class SystemSettingViewSet(DynamicModelViewSet):
    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [IsAdminRole()]
        return [AllowAny()]

    def get_object(self):
        from django.shortcuts import get_object_or_404
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]
        if str(pk).isdigit():
            return get_object_or_404(SystemSetting, pk=pk)
        return get_object_or_404(SystemSetting, hashid=pk)

    def list(self, request, *args, **kwargs):
        defaults = {
            'shipping_fee': '10.00',
            'delivery_dates': '',
            'self_collect_places': ''
        }
        for key, val in defaults.items():
            if not SystemSetting.objects.filter(key=key).exists():
                SystemSetting.objects.create(key=key, value=val)
        return super().list(request, *args, **kwargs)

class OrderViewSet(DynamicModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        from django.shortcuts import get_object_or_404
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]
        if str(pk).isdigit():
            return get_object_or_404(Order, pk=pk)
        return get_object_or_404(Order, hashid=pk)

    def get_queryset(self):
        if self.action in ['admin_orders', 'admin_dashboard', 'update_status']:
            return Order.objects.all().order_by('-create_at')
        if self.request.user.is_authenticated:
            return Order.objects.filter(user=self.request.user)
        if self.action in ['retrieve', 'upload_receipt']:
            return Order.objects.all()
        return Order.objects.none()

    def get_permissions(self):
        if self.action in ['admin_orders', 'admin_dashboard', 'update_status', 'update', 'partial_update', 'destroy']:
            return [IsAdminRole()]
        return [AllowAny()]

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            order = serializer.save(user=self.request.user)
        else:
            order = serializer.save()
            
        if order.promo_code:
            order.promo_code.current_uses += 1
            order.promo_code.save()

    @action(detail=True, methods=['post'])
    def upload_receipt(self, request, pk=None):
        order = self.get_object()
        receipt = request.FILES.get('receipt')
        if receipt:
            order.payment_receipt = receipt
            order.status = 'paid'
            order.save()
            return Response({'status': 'receipt uploaded'})
        return Response({'error': 'No receipt provided'}, status=400)

    @action(detail=False, methods=['get'])
    def admin_orders(self, request):
        orders = self.get_queryset()
        data = []
        for order in orders:
            items = []
            for item in order.items.all():
                items.append({
                    'product_name': item.product.name if item.product else '',
                    'quantity': item.quantity,
                    'unit_price': str(item.unit_price),
                    'total_price': str(item.total_price),
                })
            receipt_url = None
            if order.payment_receipt:
                receipt_url = request.build_absolute_uri(order.payment_receipt.url)
            data.append({
                'id': order.id,
                'hashid': order.hashid,
                'customer_name': order.customer_name,
                'mobile_number': order.mobile_number,
                'delivery_date': str(order.delivery_date),
                'delivery_address': order.delivery_address,
                'subtotal': str(order.subtotal),
                'shipping_fee': str(order.shipping_fee),
                'discount_amount': str(order.discount_amount),
                'total_amount': str(order.total_amount),
                'status': order.status,
                'create_at': str(order.create_at),
                'payment_receipt': receipt_url,
                'items': items,
            })
        return Response({'orders': data})

    @action(detail=False, methods=['get'])
    def admin_dashboard(self, request):
        from django.utils import timezone
        from datetime import timedelta
        orders = Order.objects.all()
        total_orders = orders.count()
        total_revenue = orders.exclude(status='cancelled').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        pending_orders = orders.filter(status='pending').count()
        paid_orders = orders.filter(status='paid').count()
        success_paid_orders = orders.filter(status='success_paid').count()
        delivered_orders = orders.filter(status='delivered').count()
        cancelled_orders = orders.filter(status='cancelled').count()

        today = timezone.now().date()
        today_orders = orders.filter(create_at__date=today).count()
        
        delivered_revenue = orders.filter(status='delivered').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        pending_revenue = orders.filter(status__in=['pending', 'paid', 'success_paid']).aggregate(
            total=Sum('total_amount')
        )['total'] or 0

        chart_data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_orders = orders.filter(create_at__date=day)
            day_count = day_orders.count()
            day_revenue = day_orders.exclude(status='cancelled').aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            chart_data.append({
                'date': str(day),
                'orders': day_count,
                'revenue': float(day_revenue)
            })

        return Response({
            'total_orders': total_orders,
            'total_revenue': float(total_revenue),
            'pending_orders': pending_orders,
            'paid_orders': paid_orders,
            'success_paid_orders': success_paid_orders,
            'delivered_orders': delivered_orders,
            'cancelled_orders': cancelled_orders,
            'today_orders': today_orders,
            'delivered_revenue': float(delivered_revenue),
            'pending_revenue': float(pending_revenue),
            'chart_data': chart_data,
        })

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        if new_status not in ['pending', 'paid', 'success_paid', 'delivered', 'cancelled']:
            return Response({'error': 'Invalid status'}, status=400)
        
        if order.status != 'cancelled' and new_status == 'cancelled':
            if order.promo_code:
                order.promo_code.current_uses = max(0, order.promo_code.current_uses - 1)
                order.promo_code.save()
                
        order.status = new_status
        order.save()
        return Response({'status': 'updated', 'new_status': new_status})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status != 'pending':
            return Response({'error': 'Only pending orders can be cancelled'}, status=400)
            
        order.status = 'cancelled'
        if order.promo_code:
            order.promo_code.current_uses = max(0, order.promo_code.current_uses - 1)
            order.promo_code.save()
        order.save()
        return Response({'status': 'cancelled'})

class HomeBannerViewSet(DynamicModelViewSet):
    queryset = HomeBanner.objects.all()
    serializer_class = HomeBannerSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_permissions(self):
        if self.action == 'upload_image':
            return [IsAdminRole()]
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [IsAdminRole()]
        return [AllowAny()]

    @action(detail=True, methods=['post'])
    def upload_image(self, request, pk=None):
        try:
            banner = HomeBanner.objects.get(pk=pk)
        except HomeBanner.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
            
        image = request.FILES.get('image')
        if image:
            banner.image = image
            banner.save()
            image_url = request.build_absolute_uri(banner.image.url)
            return Response({'status': 'image uploaded', 'image_url': image_url})
        return Response({'error': 'No image file provided'}, status=400)
