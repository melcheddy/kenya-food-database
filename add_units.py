import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nutrition_platform.settings')
django.setup()

from foods.models import Food, UnitConversion

# Define all standard Kenyan measurements
units = [
    # Volume measurements
    ('cup', 240, 'Volume'),
    ('tablespoon', 15, 'Volume'),
    ('teaspoon', 5, 'Volume'),
    ('glass', 250, 'Volume'),
    ('bottle', 500, 'Volume'),
    
    # Plate measurements (food portions)
    ('small_plate', 300, 'Food'),
    ('medium_plate', 450, 'Food'),
    ('large_plate', 600, 'Food'),
    ('bowl', 350, 'Food'),
    ('handful', 50, 'Food'),
    
    # Piece measurements
    ('piece', 50, 'Food'),
    ('small_piece', 35, 'Food'),
    ('medium_piece', 70, 'Food'),
    ('large_piece', 100, 'Food'),
    ('slice', 30, 'Food'),
]

# Add units to all foods (or specific ones)
for food in Food.objects.all():
    for unit_name, grams, unit_type in units:
        UnitConversion.objects.get_or_create(
            food=food,
            unit_name=unit_name,
            defaults={'grams': grams}
        )
        print(f"✅ Added: {food.food_name[:40]} → 1 {unit_name} = {grams}g")

print(f"\n🎉 Total units added: {UnitConversion.objects.count()}")