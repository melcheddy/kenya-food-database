import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nutrition_platform.settings')
django.setup()

from foods.models import Food
from foods.swap_suggestions import SWAP_SUGGESTIONS, get_cost_tag

# Test specific food
food_id = 512
food = Food.objects.get(id=food_id)
food_name = food.food_name
food_lower = food_name.lower()

print(f"\n{'='*60}")
print(f"Testing: {food_name}")
print(f"{'='*60}")

# Check if food has swaps
found = False
for keyword in SWAP_SUGGESTIONS:
    if keyword in food_lower:
        print(f"\n✅ MATCH: '{keyword}'")
        for swap in SWAP_SUGGESTIONS[keyword]:
            print(f"   → {swap}")
        found = True

if not found:
    print("\n❌ No direct swap found")
    print("   Need to add a swap for this food in swap_suggestions.py")

# Check cost
cost = get_cost_tag(food_name)
print(f"\n💰 Cost tag: {cost}")

# Show all keywords that might match
print(f"\n🔍 Available keywords that contain 'maize' or 'finger':")
for kw in SWAP_SUGGESTIONS:
    if 'maize' in kw or 'finger' in kw or 'ugali' in kw:
        print(f"   - {kw}")