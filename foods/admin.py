from django.contrib import admin
from .models import Category, Food, UnitConversion, RDA

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'food_count']
    search_fields = ['name']
    
    def food_count(self, obj):
        return obj.foods.count()
    food_count.short_description = 'Number of Foods'

@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ['kfct_code', 'food_name', 'category', 'energy_kcal', 'protein_g', 'iron_mg']
    list_display_links = ['food_name']
    list_filter = ['category']
    
    # THIS ADDS SEARCH BY BOTH NAME AND KFCT CODE
    search_fields = ['food_name', 'kfct_code']
    
    list_per_page = 25
    ordering = ['kfct_code']

@admin.register(UnitConversion)
class UnitConversionAdmin(admin.ModelAdmin):
    list_display = ['food', 'unit_name', 'grams']
    list_filter = ['unit_name']
    search_fields = ['food__food_name', 'food__kfct_code']

@admin.register(RDA)
class RDAAdmin(admin.ModelAdmin):
    list_display = ['gender', 'life_stage', 'energy_kcal', 'protein_g', 'iron_mg']
    list_filter = ['gender', 'life_stage']
    search_fields = ['gender', 'life_stage']