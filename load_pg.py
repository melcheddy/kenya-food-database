import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nutrition_platform.settings')
django.setup()

from foods.models import Food, Category, RDA, UnitConversion

print("Checking data...")
if Food.objects.count() == 0:
    print("Loading data from SQLite...")
    # This will be run on Render
    print("Run this in Render Shell: python manage.py loaddata all_data.json")
else:
    print(f"Already have {Food.objects.count()} foods")