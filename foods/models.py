from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

class Food(models.Model):
    # Basic info
    kfct_code = models.CharField(max_length=20, blank=True, null=True)
    food_name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='foods')
    
    # Macronutrients
    energy_kcal = models.FloatField(default=0)
    protein_g = models.FloatField(default=0)
    fat_g = models.FloatField(default=0)
    carbohydrate_g = models.FloatField(default=0)
    fiber_g = models.FloatField(default=0)
    water_g = models.FloatField(default=0)
    ash_g = models.FloatField(default=0)
    
    # Minerals
    calcium_mg = models.FloatField(default=0)
    iron_mg = models.FloatField(default=0)
    magnesium_mg = models.FloatField(default=0)
    phosphorus_mg = models.FloatField(default=0)
    potassium_mg = models.FloatField(default=0)
    sodium_mg = models.FloatField(default=0)
    zinc_mg = models.FloatField(default=0)
    copper_mg = models.FloatField(default=0)
    manganese_mg = models.FloatField(default=0)
    selenium_ug = models.FloatField(default=0)
    
    # Vitamins
    vitamin_a_rae_ug = models.FloatField(default=0)
    thiamin_mg = models.FloatField(default=0)
    riboflavin_mg = models.FloatField(default=0)
    niacin_mg = models.FloatField(default=0)
    vitamin_b6_mg = models.FloatField(default=0)
    folate_ug = models.FloatField(default=0)
    vitamin_b12_ug = models.FloatField(default=0)
    vitamin_c_mg = models.FloatField(default=0)
    
    def __str__(self):
        return self.food_name
    
    def calculate_nutrient(self, nutrient, grams):
        """Calculate nutrient amount for given grams"""
        value = getattr(self, nutrient, 0)
        return (grams / 100) * value

class UnitConversion(models.Model):
    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name='conversions')
    unit_name = models.CharField(max_length=50)
    grams = models.FloatField()
    
    def __str__(self):
        return f"{self.food.food_name} - 1 {self.unit_name} = {self.grams}g"
    
    class Meta:
        unique_together = ['food', 'unit_name']

class RDA(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    LIFE_STAGE_CHOICES = [
        ('infant', 'Infant (0-12 months)'),
        ('child_1_3', 'Child 1-3 years'),
        ('child_4_8', 'Child 4-8 years'),
        ('child_9_13', 'Child 9-13 years'),
        ('adolescent_14_18', 'Adolescent 14-18 years'),
        ('adult', 'Adult'),
        ('pregnant', 'Pregnant'),
        ('lactating', 'Lactating'),
    ]    
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    life_stage = models.CharField(max_length=20, choices=LIFE_STAGE_CHOICES)
    age_min = models.FloatField(help_text="Minimum age in years (use 0.5 for 6 months)", null=True, blank=True)
    age_max = models.FloatField(help_text="Maximum age in years (use 0.5 for 6 months)", null=True, blank=True)    
    
    # Core nutrients
    energy_kcal = models.FloatField(default=0)
    protein_g = models.FloatField(default=0)
    iron_mg = models.FloatField(default=0)
    calcium_mg = models.FloatField(default=0)
    vitamin_a_rae_ug = models.FloatField(default=0)
    folate_ug = models.FloatField(default=0)
    vitamin_c_mg = models.FloatField(default=0)
    fiber_g = models.FloatField(default=0)
    zinc_mg = models.FloatField(default=0)
    
    def __str__(self):
        age_range = ""
        if self.age_min and self.age_max:
            age_range = f" ({self.age_min}-{self.age_max} years)"
        return f"{self.get_gender_display()} - {self.get_life_stage_display()}{age_range}"
    
    class Meta:
        verbose_name = "RDA"
        verbose_name_plural = "RDAs"

# ===== NEW MEAL RECALL MODELS =====

class MealCategory(models.Model):
    """Categories like Breakfast, Lunch, Dinner, Snack"""
    name = models.CharField(max_length=50)
    order = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Meal categories"
        ordering = ['order']

class MealRecord(models.Model):
    """A 24-hour meal recall record"""
    date = models.DateField(auto_now_add=True)
    person_name = models.CharField(max_length=100, blank=True)
    person_age = models.IntegerField(null=True, blank=True)
    person_gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')], blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Meal Record - {self.date}"
    
    def total_energy(self):
        return sum(item.total_energy() for item in self.mealfooditem_set.all())
    
    def total_water_ml(self):
        water_items = self.waterintake_set.all()
        return sum(item.amount_ml for item in water_items)

class MealFoodItem(models.Model):
    """Individual food items in a meal record"""
    meal_record = models.ForeignKey(MealRecord, on_delete=models.CASCADE)
    meal_category = models.ForeignKey(MealCategory, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    amount = models.FloatField(help_text="Amount in grams")
    unit = models.CharField(max_length=50, default="grams")
    grams = models.FloatField(help_text="Actual grams consumed")
    
    def __str__(self):
        return f"{self.food.food_name} - {self.amount}{self.unit}"
    
    def total_energy(self):
        return (self.grams / 100) * self.food.energy_kcal
    
    def total_protein(self):
        return (self.grams / 100) * self.food.protein_g
    
    def total_iron(self):
        return (self.grams / 100) * self.food.iron_mg

class WaterIntake(models.Model):
    """Water consumption tracking"""
    meal_record = models.ForeignKey(MealRecord, on_delete=models.CASCADE)
    amount_ml = models.IntegerField(help_text="Amount in milliliters")
    time = models.TimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Water: {self.amount_ml}ml"
    
    def to_glasses(self):
        """Convert to standard glasses (250ml)"""
        return round(self.amount_ml / 250, 1)