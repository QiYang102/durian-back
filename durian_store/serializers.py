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
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    shipping_fee = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    
    class Meta:
        model = Order
        name = 'order'
        fields = '__all__'

    def create(self, validated_data):
        from decimal import Decimal
        from django.utils import timezone
        
        items_data = validated_data.pop('items_data', [])
        
        subtotal = Decimal('0.00')
        order_items = []
        for item_data in items_data:
            product_hashid = item_data.get('product')
            product = Product.objects.get(hashid=product_hashid) if product_hashid else None
            if product:
                quantity = int(item_data.get('quantity', 1))
                unit_price = product.price
                total_price = unit_price * quantity
                subtotal += total_price
                order_items.append({
                    'product': product,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': total_price
                })
        
        delivery_address = validated_data.get('delivery_address', '')
        if delivery_address.startswith('Self Collect'):
            shipping_fee = Decimal('0.00')
        else:
            # In a real app we'd fetch this from SystemSetting, defaulting to 10
            shipping_fee = Decimal('10.00')
            
        discount_amount = Decimal('0.00')
        promo = validated_data.get('promo_code')
        if promo:
            if promo.current_uses < promo.max_uses:
                if promo.discount_type == 'percentage':
                    discount_amount = (subtotal * promo.discount_value) / Decimal('100.00')
                elif promo.discount_type == 'fixed':
                    discount_amount = promo.discount_value
                elif promo.discount_type == 'free_shipping':
                    discount_amount = shipping_fee
                    
                if discount_amount > subtotal + shipping_fee:
                    discount_amount = subtotal + shipping_fee
            else:
                validated_data['promo_code'] = None
                
        total_amount = subtotal + shipping_fee - discount_amount
        
        validated_data['subtotal'] = subtotal
        validated_data['shipping_fee'] = shipping_fee
        validated_data['discount_amount'] = discount_amount
        validated_data['total_amount'] = total_amount
        
        order = super().create(validated_data)
        for item in order_items:
            OrderItem.objects.create(
                order=order, 
                product=item['product'], 
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                total_price=item['total_price']
            )
        return order

class HomeBannerSerializer(DynamicModelSerializer):
    class Meta:
        model = HomeBanner
        name = 'home_banner'
        fields = '__all__'
