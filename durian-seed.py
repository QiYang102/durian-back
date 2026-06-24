import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chase.settings.django')
django.setup()

from django.contrib.auth import get_user_model
from durian_store.models import Category, Product, PromoCode
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

from core.models import Tenant

tenant, _ = Tenant.objects.get_or_create(name='Durian Store')

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@durianisok.com', 'admin123', tenant=tenant)
    print("Created superuser: admin / admin123")
else:
    print("Superuser 'admin' already exists.")

fresh_cat, _ = Category.objects.get_or_create(
    name="Fresh Durian",
    defaults={'description': "Freshly dropped premium durians from our farm."}
)
products_cat, _ = Category.objects.get_or_create(
    name="Durian Products",
    defaults={'description': "Delicious treats made from real durian flesh."}
)

durians = [
    ("Musang King Whole", "Premium Grade A Musang King with signature bittersweet taste and creamy texture.", 120.00, "1kg", fresh_cat, True),
    ("Musang King Packet", "Freshly peeled Musang King flesh, vacuum sealed for freshness.", 65.00, "400g", fresh_cat, False),
    ("Black Thorn Whole", "The most sought-after Black Thorn with rosy-orange flesh and complex flavor profile.", 150.00, "1kg", fresh_cat, True),
    ("D24 Whole", "Classic D24 with thick, creamy, and sweet flesh with a hint of bitterness.", 55.00, "1kg", fresh_cat, False),
    ("Durian Crepe", "Handmade thin crepes filled with fresh durian cream.", 28.00, "6 pieces", products_cat, True),
    ("Durian Mochi", "Soft and chewy Japanese style mochi stuffed with real durian.", 22.00, "8 pieces", products_cat, False),
]

for name, desc, price, weight, cat, featured in durians:
    Product.objects.get_or_create(
        name=name,
        defaults={
            'description': desc,
            'price': price,
            'weight': weight,
            'category': cat,
            'is_featured': featured
        }
    )
print("Seeded product catalog.")

now = timezone.now()
PromoCode.objects.get_or_create(
    name='DURIAN10',
    defaults={
        'discount_type': 'percentage',
        'discount_value': 10.00,
        'valid_from': now,
        'valid_until': now + timedelta(days=365),
        'max_uses': 1000
    }
)
print("Seeded promo code 'DURIAN10'.")
print("Seed complete!")
