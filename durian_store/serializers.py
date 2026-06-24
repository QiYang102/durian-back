from dynamic_rest.serializers import DynamicModelSerializer
from .models import Category, Product, PromoCode, Order, OrderItem, SystemSetting, HomeBanner
from dynamic_rest.fields import DynamicRelationField
from rest_framework import serializers

class CategorySerializer(DynamicModelSerializer):
    class Meta:
        model = Category
        name = 'category'
        fields = '__all__'

class ProductSerializer(DynamicModelSerializer):
    category = DynamicRelationField('CategorySerializer', embed=True)
    
    class Meta:
        model = Product
        name = 'product'
        fields = '__all__'

class PromoCodeSerializer(DynamicModelSerializer):
    class Meta:
        model = PromoCode
        name = 'promo_code'
        fields = '__all__'

class SystemSettingSerializer(DynamicModelSerializer):
    class Meta:
        model = SystemSetting
        name = 'system_setting'
        fields = '__all__'

class OrderItemSerializer(DynamicModelSerializer):
    product = DynamicRelationField('ProductSerializer', embed=True)
    class Meta:
        model = OrderItem
        name = 'order_item'
        fields = '__all__'

class OrderSerializer(DynamicModelSerializer):
    items_data = serializers.JSONField(write_only=True, required=False)
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        name = 'order'
        fields = '__all__'

    def create(self, validated_data):
        items_data = validated_data.pop('items_data', [])
        order = super().create(validated_data)
        for item_data in items_data:
            product_hashid = item_data.get('product')
            product = Product.objects.get(hashid=product_hashid) if product_hashid else None
            if product:
                OrderItem.objects.create(
                    order=order, 
                    product=product, 
                    quantity=item_data.get('quantity', 1),
                    unit_price=item_data.get('unit_price', 0),
                    total_price=item_data.get('total_price', 0)
                )
        return order

class HomeBannerSerializer(DynamicModelSerializer):
    class Meta:
        model = HomeBanner
        name = 'home_banner'
        fields = '__all__'
