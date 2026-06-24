from django.db import models
from core.base_model import AbstractBaseModel
from django.contrib.auth import get_user_model

User = get_user_model()

class Category(AbstractBaseModel):
    description = models.TextField(blank=True)
    image = models.URLField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Categories'

class Product(AbstractBaseModel):
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    weight = models.CharField(max_length=50)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    image = models.URLField(blank=True, null=True)
    is_featured = models.BooleanField(default=False)

class PromoCode(AbstractBaseModel):
    discount_type = models.CharField(max_length=20, choices=[('percentage', 'Percentage'), ('fixed', 'Fixed')])
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    max_uses = models.IntegerField(default=1)
    current_uses = models.IntegerField(default=0)

class Order(AbstractBaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='durian_orders', null=True, blank=True)
    mobile_number = models.CharField(max_length=20)
    delivery_date = models.DateField()
    delivery_address = models.TextField()
    promo_code = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_receipt = models.ImageField(upload_to='receipts/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

class OrderItem(AbstractBaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
