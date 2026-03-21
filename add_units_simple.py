import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nutrition_platform.settings')
django.setup()

from foods.models import Food, UnitConversion

# Standard measurements for all foods
units = [
    ('cup', 240),
    ('tablespoon', 15),
    ('teaspoon', 5),
    ('small_plate', 300),
    ('medium_plate', 450),
    ('large_plate', 600),
    ('bowl', 350),
    ('handful', 50),
    ('piece', 50),
    ('slice', 30),
]

count = 0
for food in Food.objects.all():
    for unit_name, grams in units:
        obj, created = UnitConversion.objects.get_or_create(
            food=food,
            unit_name=unit_name,
            defaults={'grams': grams}
        )
        if created:
            count += 1
            print(f"✅ Added: {food.food_name[:40]} → 1 {unit_name} = {grams}g")

print(f"\n🎉 Added {count} new unit conversions!")
print(f"Total unit conversions: {UnitConversion.objects.count()}")