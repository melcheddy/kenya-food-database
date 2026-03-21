import os
import django
import json

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nutrition_platform.settings')
django.setup()

from foods.models import Food, Category, RDA, UnitConversion
from django.core.serializers import deserialize

print("=" * 50)
print("📦 LOADING DATA INTO POSTGRESQL")
print("=" * 50)

# Check if data already exists
food_count = Food.objects.count()
print(f"Current foods in database: {food_count}")

if food_count == 0:
    print("\n📂 Loading data from all_data.json...")
    
    try:
        with open('all_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Load categories
        categories = [obj for obj in data if obj['model'] == 'foods.category']
        if categories:
            for obj in deserialize('json', json.dumps(categories)):
                obj.save()
            print(f"✅ Loaded {len(categories)} categories")
        
        # Load foods
        foods = [obj for obj in data if obj['model'] == 'foods.food']
        if foods:
            for obj in deserialize('json', json.dumps(foods)):
                obj.save()
            print(f"✅ Loaded {len(foods)} foods")
        
        # Load RDAs
        rdas = [obj for obj in data if obj['model'] == 'foods.rda']
        if rdas:
            for obj in deserialize('json', json.dumps(rdas)):
                obj.save()
            print(f"✅ Loaded {len(rdas)} RDA entries")
        
        # Load unit conversions
        units = [obj for obj in data if obj['model'] == 'foods.unitconversion']
        if units:
            for obj in deserialize('json', json.dumps(units)):
                obj.save()
            print(f"✅ Loaded {len(units)} unit conversions")
        
        print("\n🎉 DATA LOAD COMPLETE!")
        print(f"Total foods: {Food.objects.count()}")
        
    except Exception as e:
        print(f"❌ ERROR loading data: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"✅ Data already exists ({food_count} foods)")