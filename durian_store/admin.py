from django.contrib import admin
from .models import Category, Product, PromoCode, Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'create_at')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name',)

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_value', 'is_active', 'valid_until')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('hashid', 'user', 'mobile_number', 'status', 'total_amount', 'create_at')
    list_filter = ('status', 'create_at')
    search_fields = ('hashid', 'mobile_number')
    inlines = [OrderItemInline]
