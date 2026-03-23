from django.db import migrations

def add_traditional_foods(apps, schema_editor):
    Food = apps.get_model('foods', 'Food')
    Category = apps.get_model('foods', 'Category')
    
    # Get or create categories
    beverages_cat, _ = Category.objects.get_or_create(name='beverages')
    mixed_dishes_cat, _ = Category.objects.get_or_create(name='mixed_dishes')
    misc_cat, _ = Category.objects.get_or_create(name='miscellaneous')
    fruits_cat, _ = Category.objects.get_or_create(name='fruits')
    
    foods = [
        # Beverages
        {'food_name': 'Passion fruit juice fresh', 'category': beverages_cat, 'kfct_code': '12010', 'energy_kcal': 55, 'protein_g': 0.4, 'fat_g': 0.1, 'carbohydrate_g': 13.5, 'fiber_g': 0.2, 'iron_mg': 0.2, 'calcium_mg': 12, 'vitamin_a_rae_ug': 30, 'folate_ug': 18, 'zinc_mg': 0.15, 'vitamin_c_mg': 25},
        {'food_name': 'Mango juice fresh', 'category': beverages_cat, 'kfct_code': '12011', 'energy_kcal': 48, 'protein_g': 0.3, 'fat_g': 0.1, 'carbohydrate_g': 11.8, 'fiber_g': 0.3, 'iron_mg': 0.2, 'calcium_mg': 10, 'vitamin_a_rae_ug': 45, 'folate_ug': 12, 'zinc_mg': 0.12, 'vitamin_c_mg': 20},
        {'food_name': 'Orange juice fresh', 'category': beverages_cat, 'kfct_code': '12012', 'energy_kcal': 45, 'protein_g': 0.7, 'fat_g': 0.2, 'carbohydrate_g': 10.4, 'fiber_g': 0.2, 'iron_mg': 0.2, 'calcium_mg': 11, 'vitamin_a_rae_ug': 8, 'folate_ug': 30, 'zinc_mg': 0.1, 'vitamin_c_mg': 50},
        {'food_name': 'Busaa traditional millet beer', 'category': beverages_cat, 'kfct_code': '12013', 'energy_kcal': 45, 'protein_g': 0.8, 'fat_g': 0.1, 'carbohydrate_g': 9.5, 'fiber_g': 0.5, 'iron_mg': 0.3, 'calcium_mg': 8, 'vitamin_a_rae_ug': 0, 'folate_ug': 5, 'zinc_mg': 0.2, 'vitamin_c_mg': 0},
        {'food_name': 'Muratina traditional banana beer', 'category': beverages_cat, 'kfct_code': '12014', 'energy_kcal': 52, 'protein_g': 0.5, 'fat_g': 0.1, 'carbohydrate_g': 12.2, 'fiber_g': 0.4, 'iron_mg': 0.2, 'calcium_mg': 6, 'vitamin_a_rae_ug': 2, 'folate_ug': 8, 'zinc_mg': 0.15, 'vitamin_c_mg': 0},
        {'food_name': 'Hibiscus tea karkade', 'category': beverages_cat, 'kfct_code': '12018', 'energy_kcal': 15, 'protein_g': 0.3, 'fat_g': 0, 'carbohydrate_g': 3.8, 'fiber_g': 0.2, 'iron_mg': 0.4, 'calcium_mg': 25, 'vitamin_a_rae_ug': 12, 'folate_ug': 8, 'zinc_mg': 0.1, 'vitamin_c_mg': 18},
        {'food_name': 'Ginger tea tangawizi', 'category': beverages_cat, 'kfct_code': '12019', 'energy_kcal': 18, 'protein_g': 0.2, 'fat_g': 0, 'carbohydrate_g': 4.5, 'fiber_g': 0.1, 'iron_mg': 0.2, 'calcium_mg': 8, 'vitamin_a_rae_ug': 0, 'folate_ug': 3, 'zinc_mg': 0.08, 'vitamin_c_mg': 12},
        
        # Traditional Mixed Dishes
        {'food_name': 'Aliya fish stew Luo', 'category': mixed_dishes_cat, 'kfct_code': '15085', 'energy_kcal': 145, 'protein_g': 18.5, 'fat_g': 6.8, 'carbohydrate_g': 2.5, 'fiber_g': 0.5, 'iron_mg': 2.8, 'calcium_mg': 45, 'vitamin_a_rae_ug': 8, 'folate_ug': 12, 'zinc_mg': 1.2, 'vitamin_c_mg': 12},
        {'food_name': 'Nyoyo maize and beans Luo', 'category': mixed_dishes_cat, 'kfct_code': '15086', 'energy_kcal': 168, 'protein_g': 7.5, 'fat_g': 3.2, 'carbohydrate_g': 26.5, 'fiber_g': 8.5, 'iron_mg': 2.5, 'calcium_mg': 35, 'vitamin_a_rae_ug': 2, 'folate_ug': 45, 'zinc_mg': 1.1, 'vitamin_c_mg': 4},
        {'food_name': 'Sambusa vegetable Somali', 'category': mixed_dishes_cat, 'kfct_code': '15089', 'energy_kcal': 310, 'protein_g': 8.2, 'fat_g': 12.5, 'carbohydrate_g': 38.5, 'fiber_g': 5.5, 'iron_mg': 3.2, 'calcium_mg': 48, 'vitamin_a_rae_ug': 125, 'folate_ug': 48, 'zinc_mg': 1.5, 'vitamin_c_mg': 22},
        {'food_name': 'Sambusa meat Somali', 'category': mixed_dishes_cat, 'kfct_code': '15090', 'energy_kcal': 425, 'protein_g': 16.5, 'fat_g': 22.5, 'carbohydrate_g': 38.5, 'fiber_g': 3.2, 'iron_mg': 8.5, 'calcium_mg': 42, 'vitamin_a_rae_ug': 8, 'folate_ug': 18, 'zinc_mg': 2.8, 'vitamin_c_mg': 6},
        {'food_name': 'Wali wa nazi coconut rice Coastal', 'category': mixed_dishes_cat, 'kfct_code': '15092', 'energy_kcal': 195, 'protein_g': 2.8, 'fat_g': 8.5, 'carbohydrate_g': 28.5, 'fiber_g': 0.8, 'iron_mg': 0.5, 'calcium_mg': 12, 'vitamin_a_rae_ug': 3, 'folate_ug': 12, 'zinc_mg': 0.5, 'vitamin_c_mg': 2},
        
        # Insects
        {'food_name': 'Cricket fresh raw', 'category': misc_cat, 'kfct_code': '14005', 'energy_kcal': 185, 'protein_g': 16.5, 'fat_g': 8.5, 'carbohydrate_g': 2.5, 'fiber_g': 2.5, 'iron_mg': 4.2, 'calcium_mg': 58, 'vitamin_a_rae_ug': 12, 'folate_ug': 22, 'zinc_mg': 3.5, 'vitamin_c_mg': 2.5},
        {'food_name': 'Caterpillar mopane dry', 'category': misc_cat, 'kfct_code': '14006', 'energy_kcal': 485, 'protein_g': 35.5, 'fat_g': 28.5, 'carbohydrate_g': 6.5, 'fiber_g': 5.5, 'iron_mg': 8.5, 'calcium_mg': 85, 'vitamin_a_rae_ug': 18, 'folate_ug': 35, 'zinc_mg': 4.2, 'vitamin_c_mg': 1.5},
        
        # Additional Fruits
        {'food_name': 'Soursop raw', 'category': fruits_cat, 'kfct_code': '5041', 'energy_kcal': 66, 'protein_g': 1.0, 'fat_g': 0.3, 'carbohydrate_g': 16.5, 'fiber_g': 3.5, 'iron_mg': 0.6, 'calcium_mg': 14, 'vitamin_a_rae_ug': 0, 'folate_ug': 12, 'zinc_mg': 0.2, 'vitamin_c_mg': 20},
        {'food_name': 'Breadfruit raw', 'category': fruits_cat, 'kfct_code': '5042', 'energy_kcal': 103, 'protein_g': 1.1, 'fat_g': 0.3, 'carbohydrate_g': 26.5, 'fiber_g': 4.2, 'iron_mg': 0.5, 'calcium_mg': 18, 'vitamin_a_rae_ug': 2, 'folate_ug': 15, 'zinc_mg': 0.2, 'vitamin_c_mg': 19},
        {'food_name': 'Star fruit raw', 'category': fruits_cat, 'kfct_code': '5043', 'energy_kcal': 31, 'protein_g': 0.8, 'fat_g': 0.2, 'carbohydrate_g': 6.5, 'fiber_g': 2.5, 'iron_mg': 0.3, 'calcium_mg': 8, 'vitamin_a_rae_ug': 2, 'folate_ug': 10, 'zinc_mg': 0.1, 'vitamin_c_mg': 35},
    ]
    
    for food_data in foods:
        Food.objects.get_or_create(
            food_name=food_data['food_name'],
            defaults=food_data
        )

def reverse_func(apps, schema_editor):
    Food = apps.get_model('foods', 'Food')
    names = ['Passion fruit juice fresh', 'Mango juice fresh', 'Orange juice fresh', 'Busaa traditional millet beer', 'Muratina traditional banana beer', 'Hibiscus tea karkade', 'Ginger tea tangawizi', 'Aliya fish stew Luo', 'Nyoyo maize and beans Luo', 'Sambusa vegetable Somali', 'Sambusa meat Somali', 'Wali wa nazi coconut rice Coastal', 'Cricket fresh raw', 'Caterpillar mopane dry', 'Soursop raw', 'Breadfruit raw', 'Star fruit raw']
    Food.objects.filter(food_name__in=names).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('foods', '0004_mealcategory_mealrecord_mealfooditem_waterintake'),
    ]

    operations = [
        migrations.RunPython(add_traditional_foods, reverse_func),
    ]