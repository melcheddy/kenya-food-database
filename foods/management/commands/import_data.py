import csv
from django.core.management.base import BaseCommand
from foods.models import Category, Food

class Command(BaseCommand):
    help = 'Import foods from KFCT CSV file'
    
    def handle(self, *args, **options):
        csv_file = 'kfct_complete.csv'
        
        self.stdout.write(f"📂 Importing from {csv_file}...")
        
        # Clear existing data
        Food.objects.all().delete()
        Category.objects.all().delete()
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            foods_created = 0
            categories_created = set()
            
            for row in reader:
                # Get or create category
                category_name = row.get('category', 'Uncategorized')
                category, _ = Category.objects.get_or_create(name=category_name)
                categories_created.add(category_name)
                
                # Create food with all fields
                food = Food(
                    kfct_code=row.get('kfct_code', ''),
                    food_name=row.get('food_name', ''),
                    category=category,
                    energy_kcal=float(row.get('energy_kcal', 0) or 0),
                    protein_g=float(row.get('protein_g', 0) or 0),
                    fat_g=float(row.get('fat_g', 0) or 0),
                    carbohydrate_g=float(row.get('carbohydrate_g', 0) or 0),
                    fiber_g=float(row.get('fiber_g', 0) or 0),
                    water_g=float(row.get('water_g', 0) or 0),
                    ash_g=float(row.get('ash_g', 0) or 0),
                    calcium_mg=float(row.get('calcium_mg', 0) or 0),
                    iron_mg=float(row.get('iron_mg', 0) or 0),
                    magnesium_mg=float(row.get('magnesium_mg', 0) or 0),
                    phosphorus_mg=float(row.get('phosphorus_mg', 0) or 0),
                    potassium_mg=float(row.get('potassium_mg', 0) or 0),
                    sodium_mg=float(row.get('sodium_mg', 0) or 0),
                    zinc_mg=float(row.get('zinc_mg', 0) or 0),
                    copper_mg=float(row.get('copper_mg', 0) or 0),
                    manganese_mg=float(row.get('manganese_mg', 0) or 0),
                    selenium_ug=float(row.get('selenium_ug', 0) or 0),
                    vitamin_a_rae_ug=float(row.get('vitamin_a_rae_ug', 0) or 0),
                    thiamin_mg=float(row.get('thiamin_mg', 0) or 0),
                    riboflavin_mg=float(row.get('riboflavin_mg', 0) or 0),
                    niacin_mg=float(row.get('niacin_mg', 0) or 0),
                    vitamin_b6_mg=float(row.get('vitamin_b6_mg', 0) or 0),
                    folate_ug=float(row.get('folate_ug', 0) or 0),
                    vitamin_b12_ug=float(row.get('vitamin_b12_ug', 0) or 0),
                    vitamin_c_mg=float(row.get('vitamin_c_mg', 0) or 0),
                )
                food.save()
                foods_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✅ Imported {foods_created} foods'))
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(categories_created)} categories'))