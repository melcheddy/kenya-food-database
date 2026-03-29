from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_exempt  # ← ADD THIS LINE
from .models import Food, Category, UnitConversion, SearchQuery
import json
import os
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from django.http import HttpResponse

def get_cost_tag(food_name):
    """Determine if a food is affordable, medium, or high cost based on name"""
    food_name_lower = food_name.lower()
    
    # Affordable foods
    affordable_keywords = ['maize', 'beans', 'sukuma', 'cabbage', 'dagaa', 'omena', 
                           'sweet potato', 'cassava', 'spinach', 'amaranth', 'millet',
                           'sorghum', 'githeri', 'mukimo', 'chapati', 'ugali']
    
    # Expensive foods
    expensive_keywords = ['beef', 'lamb', 'pork', 'chicken', 'fish', 'milk', 'cheese',
                          'butter', 'ghee', 'yoghurt', 'sausage', 'pilau', 'biryani',
                          'samosa', 'cake', 'biscuit', 'bread', 'soda', 'juice']
    
    for kw in affordable_keywords:
        if kw in food_name_lower:
            return 'low'
    
    for kw in expensive_keywords:
        if kw in food_name_lower:
            return 'high'
    
    return 'medium'

# ========== SWAP SUGGESTIONS ==========
SWAP_SUGGESTIONS = {
    'maize': [
        {'name': 'whole maize flour', 'benefit': '3x more fiber and iron than refined maize'},
        {'name': 'sorghum', 'benefit': 'Higher iron content, good for anemia prevention'},
        {'name': 'finger millet (wimbi)', 'benefit': 'Rich in calcium and iron'}
    ],
    'rice': [
        {'name': 'brown rice', 'benefit': 'More fiber, B vitamins, and minerals'},
        {'name': 'sorghum', 'benefit': 'Higher iron and protein content'},
        {'name': 'finger millet', 'benefit': 'Excellent calcium source'}
    ],
    'beans': [
        {'name': 'green grams (ndengu)', 'benefit': 'Easier to digest, rich in iron'},
        {'name': 'lentils', 'benefit': 'Cook faster, high in folate and iron'},
        {'name': 'soybeans', 'benefit': 'Complete protein, high iron content'}
    ],
    'sukuma': [
        {'name': 'amaranth (terere)', 'benefit': 'Higher iron and calcium than sukuma'},
        {'name': 'spider plant (saget)', 'benefit': 'Rich in iron and protein'},
        {'name': 'kale (kanzera)', 'benefit': 'Similar nutrients, different taste'}
    ],
    'chapati': [
        {'name': 'whole wheat chapati', 'benefit': 'More fiber and minerals'},
        {'name': 'multigrain chapati', 'benefit': 'Added nutrients from millet and sorghum'},
        {'name': 'ugali with sukuma', 'benefit': 'Complete meal with more nutrients'}
    ],
    'beef': [
        {'name': 'fish (omena/dagaa)', 'benefit': 'Lower fat, rich in calcium and iron'},
        {'name': 'beans', 'benefit': 'Affordable plant protein with iron'},
        {'name': 'chicken without skin', 'benefit': 'Lower saturated fat'}
    ],
    'milk': [
        {'name': 'fermented milk (maziwa lala)', 'benefit': 'Easier digestion, probiotics'},
        {'name': 'fortified milk', 'benefit': 'Added vitamin A and D'},
        {'name': 'yoghurt', 'benefit': 'Probiotics, easier digestion'}
    ],
    'oil': [
        {'name': 'red palm oil', 'benefit': 'Rich in vitamin A'},
        {'name': 'olive oil', 'benefit': 'Heart-healthy monounsaturated fats'},
        {'name': 'use less oil', 'benefit': 'Reduce calories and fat intake'}
    ]
}

# ========== NUTRIENT SWAPS ==========
NUTRIENT_SWAPS = {
    'low_iron': [
        ('sukuma wiki', 'Excellent iron source, affordable'),
        ('beans', 'Rich in iron and protein'),
        ('dagaa omena', 'High iron and calcium'),
        ('amaranth (terere)', 'Very high iron content'),
        ('beef liver', 'Concentrated iron source')
    ],
    'low_fiber': [
        ('whole maize flour', '3x more fiber than refined'),
        ('beans', 'Excellent fiber source'),
        ('sweet potato', 'Good fiber content'),
        ('githeri', 'Mixed maize and beans for fiber')
    ],
    'low_calcium': [
        ('dagaa omena', 'Eaten with bones for calcium'),
        ('milk', 'Excellent calcium source'),
        ('amaranth (terere)', 'High calcium leafy green'),
        ('finger millet (wimbi)', 'Rich in calcium')
    ]
}

def home(request):
    """Homepage with search"""
    # Get top 10 most searched foods
    from .models import SearchQuery
    popular_searches = SearchQuery.objects.all().order_by('-count')[:10]
    
    return render(request, 'foods/home.html', {
        'popular_searches': popular_searches,
    })

def search_foods(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    
    # ===== TRACK SEARCH QUERY =====
    if query:
        from .models import SearchQuery
        search_obj, created = SearchQuery.objects.get_or_create(query=query.lower())
        if not created:
            search_obj.count += 1
            search_obj.save()
    # ===== END TRACKING =====
    
    foods = Food.objects.all()
    
    if query:
        foods = foods.filter(food_name__icontains=query)
    
    if category_id:
        foods = foods.filter(category_id=category_id)
    
    categories = Category.objects.all().order_by('name')
    
    return render(request, 'foods/search_results.html', {
        'foods': foods,
        'query': query,
        'categories': categories,
        'selected_category': int(category_id) if category_id else None
    })

def food_detail(request, food_id):
    """Show detailed nutrient information for a specific food"""
    try:
        food = Food.objects.get(id=food_id)

        if 'viewed_foods' not in request.session:
            request.session['viewed_foods'] = []
        
        viewed = request.session['viewed_foods']
        viewed.append(food.food_name)
        request.session['viewed_foods'] = viewed[-10:]
        
        affordable_keywords = ['maize', 'beans', 'sukuma', 'cabbage', 'dagaa', 'omena', 
                               'sweet potato', 'cassava', 'spinach', 'amaranth']
        
        affordable_count = 0
        for food_name in viewed:
            for kw in affordable_keywords:
                if kw in food_name.lower():
                    affordable_count += 1
                    break
        
        is_budget_conscious = affordable_count >= 4
        print(f"Budget-conscious: {is_budget_conscious} (viewed {affordable_count} affordable foods)")
        
        current_cost = get_cost_tag(food.food_name)
        
        swap_suggestions = []
        food_name_lower = food.food_name.lower()
        
        for keyword, swaps in SWAP_SUGGESTIONS.items():
            if keyword in food_name_lower:
                for swap in swaps:
                    if isinstance(swap, dict):
                        swap_name = swap.get('name', '')
                        benefit = swap.get('benefit', '')
                    elif isinstance(swap, (list, tuple)) and len(swap) >= 2:
                        swap_name = swap[0]
                        benefit = swap[1]
                    else:
                        continue
                        
                    try:
                        swap_food = Food.objects.filter(food_name__icontains=swap_name).first()
                        if swap_food and swap_food.id != food.id:
                            swap_suggestions.append({
                                'name': swap_food.food_name,
                                'id': swap_food.id,
                                'benefit': benefit
                            })
                    except:
                        pass
        
        if current_cost == 'high':
            affordable_swaps = [
                ('beans', 'Affordable plant protein — 1/4 the price of meat'),
                ('sukuma wiki', 'Iron-rich vegetable, very affordable'),
                ('dagaa omena', 'Calcium-rich fish, much cheaper than beef'),
                ('whole maize flour', 'Nutritious staple, budget-friendly'),
                ('cabbage', 'Vitamin-rich, very affordable'),
            ]
            for swap_name, benefit in affordable_swaps:
                try:
                    swap_food = Food.objects.filter(food_name__icontains=swap_name).first()
                    if swap_food and swap_food.id != food.id:
                        if not any(s['id'] == swap_food.id for s in swap_suggestions):
                            swap_suggestions.append({
                                'name': swap_food.food_name,
                                'id': swap_food.id,
                                'benefit': f'💰 Affordable alternative — {benefit}'
                            })
                except:
                    pass
        
        if len(swap_suggestions) < 3:
            if food.iron_mg < 2.0:
                for swap_name, benefit in NUTRIENT_SWAPS['low_iron']:
                    try:
                        swap_food = Food.objects.filter(food_name__icontains=swap_name).first()
                        if swap_food and swap_food.id != food.id:
                            if not any(s['id'] == swap_food.id for s in swap_suggestions):
                                swap_suggestions.append({
                                    'name': swap_food.food_name,
                                    'id': swap_food.id,
                                    'benefit': f'🍳 High in iron — {benefit}'
                                })
                    except:
                        pass
            
            if food.fiber_g < 3.0 and len(swap_suggestions) < 3:
                for swap_name, benefit in NUTRIENT_SWAPS['low_fiber']:
                    try:
                        swap_food = Food.objects.filter(food_name__icontains=swap_name).first()
                        if swap_food and swap_food.id != food.id:
                            if not any(s['id'] == swap_food.id for s in swap_suggestions):
                                swap_suggestions.append({
                                    'name': swap_food.food_name,
                                    'id': swap_food.id,
                                    'benefit': f'🌾 High in fiber — {benefit}'
                                })
                    except:
                        pass
        
        swap_suggestions = swap_suggestions[:3]
        
        return render(request, 'foods/food_detail.html', {
            'food': food,
            'swap_suggestions': swap_suggestions,
            'cost_tag': current_cost,
        })
        
    except Exception as e:
        print(f"ERROR in food_detail for ID {food_id}: {e}")
        import traceback
        traceback.print_exc()
        return render(request, 'foods/error.html', {
            'error': str(e),
            'food_id': food_id
        }, status=500)
          
def export_food_excel(request, food_id):
    """Export a single food's nutrient data as Excel file for nutritionists"""
    try:
        food = Food.objects.get(id=food_id)
        
        # Create a new workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"{food.food_name[:25]} Nutrition"
        
        # Define styles
        header_font = Font(bold=True, color="FFFFFF", size=12)
        header_fill = PatternFill(start_color="2c5e2e", end_color="2c5e2e", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        category_font = Font(bold=True, size=11, color="2c5e2e")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # ========== FOOD INFO SECTION (NO MERGED CELLS) ==========
        ws['A1'] = "🇰🇪 Kenya Food Composition Database"
        ws['A1'].font = Font(bold=True, size=14)
        
        ws['A2'] = food.food_name
        ws['A2'].font = Font(bold=True, size=12, italic=True)
        
        # Category
        ws['A4'] = "Category:"
        ws['A4'].font = Font(bold=True)
        ws['B4'] = food.category.name if food.category else "Kenyan Food"
        
        # ========== NUTRIENT TABLE ==========
        ws['A6'] = "Nutrient"
        ws['B6'] = "Value per 100g"
        ws['C6'] = "Unit"
        
        # Apply header styles
        for col in ['A6', 'B6', 'C6']:
            ws[col].font = header_font
            ws[col].fill = header_fill
            ws[col].alignment = header_alignment
            ws[col].border = border
        
        # Define all nutrients
        nutrients = [
            ('🔥 Energy', food.energy_kcal, 'kcal'),
            ('💪 Protein', food.protein_g, 'g'),
            ('🧈 Total Fat', food.fat_g, 'g'),
            ('🍚 Carbohydrates', food.carbohydrate_g, 'g'),
            ('🌾 Dietary Fiber', food.fiber_g, 'g'),
            ('💧 Water', food.water_g, 'g'),
            ('🧂 Ash (Minerals)', food.ash_g, 'g'),
            ('🦴 Calcium', food.calcium_mg, 'mg'),
            ('🩸 Iron', food.iron_mg, 'mg'),
            ('✨ Magnesium', food.magnesium_mg, 'mg'),
            ('🦷 Phosphorus', food.phosphorus_mg, 'mg'),
            ('🍌 Potassium', food.potassium_mg, 'mg'),
            ('🧂 Sodium', food.sodium_mg, 'mg'),
            ('⚡ Zinc', food.zinc_mg, 'mg'),
            ('💊 Thiamin (B1)', food.thiamin_mg, 'mg'),
            ('💊 Riboflavin (B2)', food.riboflavin_mg, 'mg'),
            ('💊 Niacin (B3)', food.niacin_mg, 'mg'),
            ('🌿 Folate', food.folate_ug, 'µg'),
        ]
        
        # Write data rows
        row = 7
        for name, value, unit in nutrients:
            # Format value
            if value is None or value == 0:
                formatted_value = '0'
            elif value < 1:
                formatted_value = f'{value:.2f}'
            else:
                formatted_value = f'{value:.1f}'
            
            ws[f'A{row}'] = name
            ws[f'B{row}'] = formatted_value
            ws[f'C{row}'] = unit
            
            # Apply borders
            for col in ['A', 'B', 'C']:
                ws[f'{col}{row}'].border = border
            
            row += 1
        
        # ========== SUMMARY SECTION ==========
        row += 1
        ws[f'A{row}'] = "📊 SUMMARY"
        ws[f'A{row}'].font = Font(bold=True, size=12, color="2c5e2e")
        row += 1
        
        # RDA Note
        ws[f'A{row}'] = "Recommended Daily Allowance (RDA) Note:"
        ws[f'A{row}'].font = Font(bold=True, italic=True)
        row += 1
        ws[f'A{row}'] = "RDA values vary by age, gender, and physiological state (pregnancy, lactation)."
        ws[f'A{row}'].font = Font(size=9, color="666666")
        
        row += 2
        ws[f'A{row}'] = "💡 TYPICAL RDA FOR ADULT WOMAN (19-50 yrs):"
        ws[f'A{row}'].font = Font(bold=True)
        row += 1
        ws[f'A{row}'] = "Energy: 2100 kcal"
        ws[f'B{row}'] = "Iron: 29 mg"
        ws[f'C{row}'] = "Calcium: 1000 mg"
        row += 1
        ws[f'A{row}'] = "Protein: 46 g"
        ws[f'B{row}'] = "Folate: 400 µg"
        ws[f'C{row}'] = "Fiber: 25 g"
        
        row += 2
        ws[f'A{row}'] = "💡 TYPICAL RDA FOR ADULT MAN (19-50 yrs):"
        ws[f'A{row}'].font = Font(bold=True)
        row += 1
        ws[f'A{row}'] = "Energy: 2500 kcal"
        ws[f'B{row}'] = "Iron: 11 mg"
        ws[f'C{row}'] = "Calcium: 1000 mg"
        row += 1
        ws[f'A{row}'] = "Protein: 56 g"
        ws[f'B{row}'] = "Folate: 400 µg"
        ws[f'C{row}'] = "Fiber: 30 g"
        
        # ========== FOOTER SECTION ==========
        row += 2
        ws[f'A{row}'] = "📊 Data Source: Kenya Food Composition Tables 2018 (FAO / Ministry of Health)"
        ws[f'A{row}'].font = Font(size=9, italic=True, color="2c5e2e")
        
        row += 1
        ws[f'A{row}'] = f"📅 Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ws[f'A{row}'].font = Font(size=9)
        
        row += 1
        ws[f'A{row}'] = "⚠️ Note: Values are averages. Actual nutrient content may vary by variety, season, and preparation."
        ws[f'A{row}'].font = Font(size=8, color="856404")
        
        # Auto-adjust column widths (NO MERGED CELLS)
        for col in ['A', 'B', 'C']:
            max_length = 0
            for row_num in range(1, row + 5):
                cell_value = ws[f'{col}{row_num}'].value
                if cell_value and len(str(cell_value)) > max_length:
                    max_length = len(str(cell_value))
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[col].width = adjusted_width
        
        # Create HTTP response
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = f"{food.food_name.replace(' ', '_')}_nutrition.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        wb.save(response)
        return response
        
    except Food.DoesNotExist:
        return HttpResponse(f"Food with ID {food_id} not found", status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Error exporting data: {e}", status=500)

def nutrient_calculator(request):
    foods = Food.objects.all().order_by('food_name')
    categories = Category.objects.all()
    
    result = None
    food_selected = None
    amount = 100
    unit = 'grams'
    gender = 'female'
    age = 30
    available_units = []
    rda = None
    
    # ========== HANDLE GET PARAMETER (from redirect button) ==========
    # Check if a food was passed via GET parameter (from food detail page)
    pre_selected_food = request.GET.get('food', '')
    if pre_selected_food and not request.POST:
        try:
            food_selected = Food.objects.get(food_name=pre_selected_food)
            available_units = UnitConversion.objects.filter(food=food_selected)
        except Food.DoesNotExist:
            pass
    # ========== END GET PARAMETER HANDLING ==========
    
    if request.method == 'POST':
        food_id = request.POST.get('food_id')
        
        if not food_id:
            gender = request.POST.get('gender', 'female')
            try:
                age = int(request.POST.get('age', 30))
            except ValueError:
                age = 30
            return render(request, 'foods/calculator.html', {
                'foods': foods,
                'categories': categories,
                'food_selected': None,
                'amount': 100,
                'unit': 'grams',
                'gender': gender,
                'age': age,
                'available_units': [],
                'result': None,
                'rda': None,
            })
        
        amount = float(request.POST.get('amount', 100))
        unit = request.POST.get('unit', 'grams')
        gender = request.POST.get('gender', 'female')
        age = int(request.POST.get('age', 30))
        
        try:
            food_selected = Food.objects.get(id=food_id)
            available_units = UnitConversion.objects.filter(food=food_selected)
            
            grams = amount
            if unit != 'grams':
                try:
                    conversion = UnitConversion.objects.get(food=food_selected, unit_name=unit)
                    grams = amount * conversion.grams
                except UnitConversion.DoesNotExist:
                    grams = amount
            
            result = {
                'food_name': food_selected.food_name,
                'amount': amount,
                'unit': unit,
                'grams': grams,
                'energy_kcal': (grams / 100) * food_selected.energy_kcal,
                'protein_g': (grams / 100) * food_selected.protein_g,
                'fat_g': (grams / 100) * food_selected.fat_g,
                'carbohydrate_g': (grams / 100) * food_selected.carbohydrate_g,
                'fiber_g': (grams / 100) * food_selected.fiber_g,
                'water_g': (grams / 100) * food_selected.water_g,
                'iron_mg': (grams / 100) * food_selected.iron_mg,
                'calcium_mg': (grams / 100) * food_selected.calcium_mg,
                'magnesium_mg': (grams / 100) * food_selected.magnesium_mg,
                'phosphorus_mg': (grams / 100) * food_selected.phosphorus_mg,
                'potassium_mg': (grams / 100) * food_selected.potassium_mg,
                'sodium_mg': (grams / 100) * food_selected.sodium_mg,
                'zinc_mg': (grams / 100) * food_selected.zinc_mg,
                'vitamin_a_rae_ug': (grams / 100) * food_selected.vitamin_a_rae_ug,
                'thiamin_mg': (grams / 100) * food_selected.thiamin_mg,
                'riboflavin_mg': (grams / 100) * food_selected.riboflavin_mg,
                'niacin_mg': (grams / 100) * food_selected.niacin_mg,
                'vitamin_b6_mg': (grams / 100) * food_selected.vitamin_b6_mg,
                'folate_ug': (grams / 100) * food_selected.folate_ug,
                'vitamin_b12_ug': (grams / 100) * food_selected.vitamin_b12_ug,
                'vitamin_c_mg': (grams / 100) * food_selected.vitamin_c_mg,
            }
            
            if age < 19:
                if gender == 'female':
                    rda = {'energy_kcal': 2000, 'protein_g': 46, 'iron_mg': 15, 'calcium_mg': 1300}
                else:
                    rda = {'energy_kcal': 2400, 'protein_g': 52, 'iron_mg': 11, 'calcium_mg': 1300}
            else:
                if gender == 'female':
                    rda = {'energy_kcal': 2100, 'protein_g': 46, 'iron_mg': 29, 'calcium_mg': 1000}
                else:
                    rda = {'energy_kcal': 2500, 'protein_g': 56, 'iron_mg': 11, 'calcium_mg': 1000}
            
            result['energy_percent'] = (result['energy_kcal'] / rda['energy_kcal']) * 100
            result['iron_percent'] = (result['iron_mg'] / rda['iron_mg']) * 100 if rda['iron_mg'] > 0 else 0
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'result': result,
                    'rda': rda,
                })
            
        except Food.DoesNotExist:
            pass
    
    return render(request, 'foods/calculator.html', {
        'foods': foods,
        'categories': categories,
        'food_selected': food_selected,
        'amount': amount,
        'unit': unit,
        'gender': gender,
        'age': age,
        'available_units': available_units,
        'result': result,
        'rda': rda,
    })

def recall_24hr(request):
    """24-hour dietary recall with searchable foods and fluids"""
    foods = Food.objects.all().order_by('food_name')
    
    meals = [
        {'id': 1, 'name': 'Breakfast'},
        {'id': 2, 'name': 'Morning Snack'},
        {'id': 3, 'name': 'Lunch'},
        {'id': 4, 'name': 'Afternoon Snack'},
        {'id': 5, 'name': 'Dinner'},
        {'id': 6, 'name': 'Evening Snack'},
    ]
    
    results = None
    
    if request.method == 'POST':
        name = request.POST.get('name', '')
        age = request.POST.get('age', '')
        gender = request.POST.get('gender', 'female')
        
        total_energy = 0
        total_protein = 0
        total_iron = 0
        total_fiber = 0
        total_calcium = 0
        total_vitamin_a = 0
        total_fluid_ml = 0
        
        try:
            age = int(age) if age else 30
        except ValueError:
            age = 30
        
        fluid_ids = request.POST.getlist('fluid_id[]')
        fluid_amounts = request.POST.getlist('fluid_amount[]')
        fluid_units = request.POST.getlist('fluid_unit[]')
        
        for i in range(len(fluid_ids)):
            if fluid_ids[i] and fluid_amounts[i]:
                try:
                    amount = float(fluid_amounts[i])
                    unit = fluid_units[i]
                    
                    if unit == 'ml':
                        total_fluid_ml += amount
                    elif unit == 'cup':
                        total_fluid_ml += amount * 240
                    elif unit == 'glass':
                        total_fluid_ml += amount * 250
                    elif unit == 'bottle':
                        total_fluid_ml += amount * 500
                except (ValueError, IndexError):
                    pass
        
        for meal in meals:
            meal_id = meal['id']
            food_ids = request.POST.getlist(f'food_id_{meal_id}[]')
            amounts = request.POST.getlist(f'amount_{meal_id}[]')
            units = request.POST.getlist(f'unit_{meal_id}[]')
            
            for i in range(len(food_ids)):
                if food_ids[i] and amounts[i]:
                    try:
                        food = Food.objects.get(id=food_ids[i])
                        amount = float(amounts[i])
                        unit = units[i] if i < len(units) else 'grams'
                        
                        grams = amount
                        if unit != 'grams':
                            try:
                                conversion = UnitConversion.objects.get(food=food, unit_name=unit)
                                grams = amount * conversion.grams
                            except UnitConversion.DoesNotExist:
                                grams = amount
                        
                        total_energy += (grams / 100) * food.energy_kcal
                        total_protein += (grams / 100) * food.protein_g
                        total_iron += (grams / 100) * food.iron_mg
                        total_fiber += (grams / 100) * food.fiber_g
                        total_calcium += (grams / 100) * food.calcium_mg
                        total_vitamin_a += (grams / 100) * food.vitamin_a_rae_ug
                        total_fluid_ml += (grams / 100) * food.water_g
                        
                    except (Food.DoesNotExist, ValueError):
                        pass
        
        if age < 4:
            ai_liters = 1.3
        elif age < 9:
            ai_liters = 1.7
        elif age < 14:
            ai_liters = 2.4 if gender == 'male' else 2.1
        elif age < 19:
            ai_liters = 3.3 if gender == 'male' else 2.3
        else:
            ai_liters = 3.7 if gender == 'male' else 2.7
        
        total_fluid_l = total_fluid_ml / 1000
        fluid_percent = (total_fluid_l / ai_liters) * 100 if ai_liters > 0 else 0
        
        results = {
            'total_energy': total_energy,
            'total_protein': total_protein,
            'total_iron': total_iron,
            'total_fiber': total_fiber,
            'total_calcium': total_calcium,
            'total_vitamin_a': total_vitamin_a,
            'total_fluid_ml': total_fluid_ml,
            'total_fluid_l': total_fluid_l,
            'ai_liters': ai_liters,
            'fluid_percent': fluid_percent,
            'name': name,
            'age': age,
            'gender': gender,
        }
        
        if fluid_percent < 80:
            results['hydration_message'] = '⚠️ You might be running low on fluids. Try to drink more water throughout the day.'
        elif fluid_percent <= 120:
            results['hydration_message'] = '✅ Great job! Your hydration is on point.'
        else:
            results['hydration_message'] = '💧 You\'re well hydrated!'
        
        # RDI analysis
        if gender == 'female':
            if age < 19:
                rdi = {'energy_kcal': 2000, 'protein_g': 46, 'iron_mg': 15, 'calcium_mg': 1300}
            else:
                rdi = {'energy_kcal': 2100, 'protein_g': 46, 'iron_mg': 29, 'calcium_mg': 1000}
        else:
            if age < 19:
                rdi = {'energy_kcal': 2400, 'protein_g': 52, 'iron_mg': 11, 'calcium_mg': 1300}
            else:
                rdi = {'energy_kcal': 2500, 'protein_g': 56, 'iron_mg': 11, 'calcium_mg': 1000}
        
        results['rdi'] = rdi
        results['rdi_percentages'] = {
            'energy_percent': (total_energy / rdi['energy_kcal']) * 100,
            'protein_percent': (total_protein / rdi['protein_g']) * 100,
            'iron_percent': (total_iron / rdi['iron_mg']) * 100,
            'calcium_percent': (total_calcium / rdi['calcium_mg']) * 100,
        }
        
        results['status_messages'] = []
        
        if results['rdi_percentages']['iron_percent'] < 70:
            results['status_messages'].append({
                'nutrient': 'Iron',
                'status': 'low',
                'message': f"⚠️ Your iron intake ({total_iron:.1f}mg) is only {results['rdi_percentages']['iron_percent']:.0f}% of daily needs.",
                'suggestions': ['sukuma wiki', 'beans', 'dagaa omena']
            })
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'results': results,
                'name': name or 'there',
            })
    
    return render(request, 'foods/recall_24hr.html', {
        'foods': foods,
        'meals': meals,
        'results': results,
    })

def export_recall_excel(request):
    """Export 24-hour recall results as Excel file for nutritionists"""
    try:
        if request.method == 'POST':
            from .models import Food, UnitConversion
            from datetime import datetime
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
            from django.http import HttpResponse
            
            # Get form data
            name = request.POST.get('name', '')
            age = request.POST.get('age', '')
            gender = request.POST.get('gender', 'female')
            
            try:
                age = int(age) if age else 30
            except ValueError:
                age = 30
            
            total_energy = 0
            total_protein = 0
            total_fat = 0
            total_carbs = 0
            total_fiber = 0
            total_iron = 0
            total_calcium = 0
            total_vitamin_a = 0
            total_fluid_ml = 0
            
            food_items = []
            
            # Process meals
            meals = [
                {'id': 1, 'name': 'Breakfast'},
                {'id': 2, 'name': 'Morning Snack'},
                {'id': 3, 'name': 'Lunch'},
                {'id': 4, 'name': 'Afternoon Snack'},
                {'id': 5, 'name': 'Dinner'},
                {'id': 6, 'name': 'Evening Snack'},
            ]
            
            for meal in meals:
                meal_id = meal['id']
                food_ids = request.POST.getlist(f'food_id_{meal_id}[]')
                amounts = request.POST.getlist(f'amount_{meal_id}[]')
                units = request.POST.getlist(f'unit_{meal_id}[]')
                
                for i in range(len(food_ids)):
                    if food_ids[i] and amounts[i]:
                        try:
                            food = Food.objects.get(id=food_ids[i])
                            amount = float(amounts[i])
                            unit = units[i] if i < len(units) else 'grams'
                            
                            grams = amount
                            if unit != 'grams':
                                try:
                                    conversion = UnitConversion.objects.get(food=food, unit_name=unit)
                                    grams = amount * conversion.grams
                                except UnitConversion.DoesNotExist:
                                    pass
                            
                            energy = (grams / 100) * food.energy_kcal
                            protein = (grams / 100) * food.protein_g
                            fat = (grams / 100) * food.fat_g
                            carbs = (grams / 100) * food.carbohydrate_g
                            fiber = (grams / 100) * food.fiber_g
                            iron = (grams / 100) * food.iron_mg
                            calcium = (grams / 100) * food.calcium_mg
                            vitamin_a = (grams / 100) * food.vitamin_a_rae_ug
                            
                            total_energy += energy
                            total_protein += protein
                            total_fat += fat
                            total_carbs += carbs
                            total_fiber += fiber
                            total_iron += iron
                            total_calcium += calcium
                            total_vitamin_a += vitamin_a
                            total_fluid_ml += (grams / 100) * food.water_g
                            
                            food_items.append({
                                'meal': meal['name'],
                                'food': food.food_name,
                                'amount': amount,
                                'unit': unit,
                                'grams': grams,
                                'energy': energy,
                                'protein': protein,
                                'iron': iron,
                                'calcium': calcium
                            })
                        except (Food.DoesNotExist, ValueError):
                            pass
            
            # Process fluids
            fluid_ids = request.POST.getlist('fluid_id[]')
            fluid_amounts = request.POST.getlist('fluid_amount[]')
            fluid_units = request.POST.getlist('fluid_unit[]')
            
            fluid_items = []
            for i in range(len(fluid_ids)):
                if fluid_ids[i] and fluid_amounts[i]:
                    try:
                        amount = float(fluid_amounts[i])
                        unit = fluid_units[i]
                        
                        ml = amount
                        if unit == 'cup':
                            ml = amount * 240
                        elif unit == 'glass':
                            ml = amount * 250
                        elif unit == 'bottle':
                            ml = amount * 500
                        
                        total_fluid_ml += ml
                        
                        fluid_name = "Water"
                        if fluid_ids[i] != '9991':
                            fluid_map = {'9992': 'Black Tea', '9993': 'Milk Tea', '9994': 'Coffee',
                                        '9995': 'Orange Juice', '9996': 'Soda', '9997': 'Fermented Milk',
                                        '9998': 'Yogurt Drink', '9999': 'Fresh Juice'}
                            fluid_name = fluid_map.get(fluid_ids[i], 'Beverage')
                        
                        fluid_items.append({
                            'fluid': fluid_name,
                            'amount': amount,
                            'unit': unit,
                            'ml': ml
                        })
                    except (ValueError, IndexError):
                        pass
            
            # Calculate RDA
            if age < 19:
                if gender == 'female':
                    rda = {'energy_kcal': 2000, 'protein_g': 46, 'iron_mg': 15, 'calcium_mg': 1300}
                else:
                    rda = {'energy_kcal': 2400, 'protein_g': 52, 'iron_mg': 11, 'calcium_mg': 1300}
            else:
                if gender == 'female':
                    rda = {'energy_kcal': 2100, 'protein_g': 46, 'iron_mg': 29, 'calcium_mg': 1000}
                else:
                    rda = {'energy_kcal': 2500, 'protein_g': 56, 'iron_mg': 11, 'calcium_mg': 1000}
            
            # Calculate AI for fluids
            if age < 4:
                ai_liters = 1.3
            elif age < 9:
                ai_liters = 1.7
            elif age < 14:
                ai_liters = 2.4 if gender == 'male' else 2.1
            elif age < 19:
                ai_liters = 3.3 if gender == 'male' else 2.3
            else:
                ai_liters = 3.7 if gender == 'male' else 2.7
            
            total_fluid_l = total_fluid_ml / 1000
            fluid_percent = (total_fluid_l / ai_liters) * 100 if ai_liters > 0 else 0
            
            # Create workbook
            wb = openpyxl.Workbook()
            
            # ========== SHEET 1: SUMMARY ==========
            ws_summary = wb.active
            ws_summary.title = "Nutrition Summary"
            
            # Title (without using merge - use simple cells)
            ws_summary['A1'] = "24-HOUR DIETARY RECALL REPORT"
            ws_summary['A1'].font = Font(bold=True, size=16)
            
            # Patient info
            ws_summary['A3'] = "Patient Information"
            ws_summary['A3'].font = Font(bold=True, size=12, color="2c5e2e")
            ws_summary['A4'] = "Name:"
            ws_summary['B4'] = name or "Not provided"
            ws_summary['A5'] = "Age:"
            ws_summary['B5'] = age
            ws_summary['A6'] = "Gender:"
            ws_summary['B6'] = "Female" if gender == 'female' else "Male"
            ws_summary['A7'] = "Date:"
            ws_summary['B7'] = datetime.now().strftime('%Y-%m-%d %H:%M')
            
            # Total Nutrients
            ws_summary['A9'] = "Total Nutrients"
            ws_summary['A9'].font = Font(bold=True, size=12, color="2c5e2e")
            
            nutrients = [
                ('Energy (kcal)', total_energy, rda['energy_kcal'], (total_energy/rda['energy_kcal'])*100 if rda['energy_kcal'] > 0 else 0),
                ('Protein (g)', total_protein, rda['protein_g'], (total_protein/rda['protein_g'])*100 if rda['protein_g'] > 0 else 0),
                ('Iron (mg)', total_iron, rda['iron_mg'], (total_iron/rda['iron_mg'])*100 if rda['iron_mg'] > 0 else 0),
                ('Calcium (mg)', total_calcium, rda['calcium_mg'], (total_calcium/rda['calcium_mg'])*100 if rda['calcium_mg'] > 0 else 0),
                ('Fat (g)', total_fat, 'N/A', 0),
                ('Carbohydrates (g)', total_carbs, 'N/A', 0),
                ('Fiber (g)', total_fiber, 'N/A', 0),
                ('Vitamin A (µg)', total_vitamin_a, 'N/A', 0),
            ]
            
            row = 10
            for nutrient_name, value, target, percent in nutrients:
                ws_summary[f'A{row}'] = nutrient_name
                ws_summary[f'B{row}'] = f"{value:.1f}"
                if target != 'N/A':
                    ws_summary[f'C{row}'] = f"Target: {target}"
                    ws_summary[f'D{row}'] = f"{percent:.0f}%"
                    if percent < 70:
                        ws_summary[f'D{row}'].font = Font(color="dc3545", bold=True)
                row += 1
            
            # Hydration
            row += 1
            ws_summary[f'A{row}'] = "Hydration"
            ws_summary[f'A{row}'].font = Font(bold=True, size=12, color="2c5e2e")
            row += 1
            ws_summary[f'A{row}'] = "Total Fluids:"
            ws_summary[f'B{row}'] = f"{total_fluid_ml:.0f} ml ({total_fluid_l:.1f} L)"
            row += 1
            ws_summary[f'A{row}'] = "Daily Target:"
            ws_summary[f'B{row}'] = f"{ai_liters} L"
            row += 1
            ws_summary[f'A{row}'] = "Status:"
            if fluid_percent < 80:
                ws_summary[f'B{row}'] = "⚠️ Low hydration - drink more water"
                ws_summary[f'B{row}'].font = Font(color="dc3545")
            elif fluid_percent <= 120:
                ws_summary[f'B{row}'] = "✅ Well hydrated"
                ws_summary[f'B{row}'].font = Font(color="28a745")
            else:
                ws_summary[f'B{row}'] = "💧 Well hydrated"
            
            # Recommendations
            row += 2
            ws_summary[f'A{row}'] = "Recommendations"
            ws_summary[f'A{row}'].font = Font(bold=True, size=12, color="2c5e2e")
            row += 1
            
            has_recommendations = False
            if total_iron < rda['iron_mg'] * 0.7:
                ws_summary[f'A{row}'] = "⚠️ Low Iron Intake"
                ws_summary[f'B{row}'] = "Try adding: beans, sukuma wiki, dagaa omena, whole maize flour"
                ws_summary[f'B{row}'].font = Font(color="dc3545")
                row += 1
                has_recommendations = True
            if total_calcium < rda['calcium_mg'] * 0.7:
                ws_summary[f'A{row}'] = "⚠️ Low Calcium Intake"
                ws_summary[f'B{row}'] = "Try adding: milk, dagaa omena, amaranth leaves, sesame seeds"
                ws_summary[f'B{row}'].font = Font(color="dc3545")
                row += 1
                has_recommendations = True
            if total_fiber < 20:
                ws_summary[f'A{row}'] = "⚠️ Low Fiber Intake"
                ws_summary[f'B{row}'] = "Try adding: whole grains, beans, vegetables"
                ws_summary[f'B{row}'].font = Font(color="dc3545")
                row += 1
                has_recommendations = True
            
            if not has_recommendations:
                ws_summary[f'A{row}'] = "✅ Good balance! Keep up the healthy eating habits."
                ws_summary[f'A{row}'].font = Font(color="28a745")
            
            # Auto-adjust columns (NO MERGED CELLS)
            for col in ['A', 'B', 'C', 'D']:
                max_length = 0
                for row_num in range(1, row + 10):
                    cell_value = ws_summary[f'{col}{row_num}'].value
                    if cell_value and len(str(cell_value)) > max_length:
                        max_length = len(str(cell_value))
                adjusted_width = min(max_length + 2, 40)
                ws_summary.column_dimensions[col].width = adjusted_width
            
            # ========== SHEET 2: FOODS LOGGED ==========
            ws_foods = wb.create_sheet("Foods Logged")
            
            if food_items:
                headers = ['Meal', 'Food', 'Amount', 'Unit', 'Grams', 'Energy (kcal)', 'Protein (g)', 'Iron (mg)', 'Calcium (mg)']
                for col_idx, header in enumerate(headers, 1):
                    cell = ws_foods.cell(row=1, column=col_idx, value=header)
                    cell.font = Font(bold=True, color="FFFFFF")
                    cell.fill = PatternFill(start_color="2c5e2e", end_color="2c5e2e", fill_type="solid")
                    cell.alignment = Alignment(horizontal="center")
                
                for row_idx, item in enumerate(food_items, 2):
                    ws_foods.cell(row=row_idx, column=1, value=item['meal'])
                    ws_foods.cell(row=row_idx, column=2, value=item['food'])
                    ws_foods.cell(row=row_idx, column=3, value=item['amount'])
                    ws_foods.cell(row=row_idx, column=4, value=item['unit'])
                    ws_foods.cell(row=row_idx, column=5, value=f"{item['grams']:.1f}")
                    ws_foods.cell(row=row_idx, column=6, value=f"{item['energy']:.1f}")
                    ws_foods.cell(row=row_idx, column=7, value=f"{item['protein']:.1f}")
                    ws_foods.cell(row=row_idx, column=8, value=f"{item['iron']:.1f}")
                    ws_foods.cell(row=row_idx, column=9, value=f"{item['calcium']:.0f}")
                
                # Auto-adjust columns
                for col_idx in range(1, 10):
                    max_length = 0
                    for row_num in range(1, len(food_items) + 2):
                        cell_value = ws_foods.cell(row=row_num, column=col_idx).value
                        if cell_value and len(str(cell_value)) > max_length:
                            max_length = len(str(cell_value))
                    adjusted_width = min(max_length + 2, 30)
                    ws_foods.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = adjusted_width
            
            # ========== SHEET 3: FLUIDS LOGGED ==========
            ws_fluids = wb.create_sheet("Fluids Logged")
            
            if fluid_items:
                headers = ['Beverage', 'Amount', 'Unit', 'Milliliters (ml)']
                for col_idx, header in enumerate(headers, 1):
                    cell = ws_fluids.cell(row=1, column=col_idx, value=header)
                    cell.font = Font(bold=True, color="FFFFFF")
                    cell.fill = PatternFill(start_color="17a2b8", end_color="17a2b8", fill_type="solid")
                    cell.alignment = Alignment(horizontal="center")
                
                for row_idx, item in enumerate(fluid_items, 2):
                    ws_fluids.cell(row=row_idx, column=1, value=item['fluid'])
                    ws_fluids.cell(row=row_idx, column=2, value=item['amount'])
                    ws_fluids.cell(row=row_idx, column=3, value=item['unit'])
                    ws_fluids.cell(row=row_idx, column=4, value=f"{item['ml']:.0f}")
                
                # Auto-adjust columns
                for col_idx in range(1, 5):
                    max_length = 0
                    for row_num in range(1, len(fluid_items) + 2):
                        cell_value = ws_fluids.cell(row=row_num, column=col_idx).value
                        if cell_value and len(str(cell_value)) > max_length:
                            max_length = len(str(cell_value))
                    adjusted_width = min(max_length + 2, 25)
                    ws_fluids.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = adjusted_width
            
            # Create response
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            filename = f"nutrition_recall_{name.replace(' ', '_') if name else 'report'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            wb.save(response)
            return response
            
        else:
            return HttpResponse("Invalid request method", status=400)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Error exporting recall data: {str(e)}", status=500)

def compare_foods(request):
    import traceback
    foods = Food.objects.all().order_by('food_name')
    
    food1 = None
    food2 = None
    comparison = None
    messages = []
    
    if request.method == 'POST':
        food1_id = request.POST.get('food1')
        food2_id = request.POST.get('food2')
        
        if food1_id and food2_id:
            try:
                food1 = Food.objects.get(id=food1_id)
                food2 = Food.objects.get(id=food2_id)
                
                nutrients = [
                    {'name': 'Energy (kcal)', 'key': 'energy_kcal', 'unit': 'kcal', 'higher_is': 'better'},
                    {'name': 'Protein (g)', 'key': 'protein_g', 'unit': 'g', 'higher_is': 'better'},
                    {'name': 'Fiber (g)', 'key': 'fiber_g', 'unit': 'g', 'higher_is': 'better'},
                    {'name': 'Iron (mg)', 'key': 'iron_mg', 'unit': 'mg', 'higher_is': 'better'},
                    {'name': 'Calcium (mg)', 'key': 'calcium_mg', 'unit': 'mg', 'higher_is': 'better'},
                ]
                
                comparison = []
                for n in nutrients:
                    val1 = getattr(food1, n['key'], 0)
                    val2 = getattr(food2, n['key'], 0)
                    
                    # Determine winner
                    if n['higher_is'] == 'better':
                        if val1 > val2:
                            winner = 1
                        elif val2 > val1:
                            winner = 2
                        else:
                            winner = 0
                    else:
                        winner = 0
                    
                    # Calculate percentage for visual bar
                    max_val = max(val1, val2)
                    if max_val > 0:
                        pct1 = (val1 / max_val) * 100
                        pct2 = (val2 / max_val) * 100
                    else:
                        pct1 = 0
                        pct2 = 0
                    
                    comparison.append({
                        'name': n['name'],
                        'key': n['key'],
                        'unit': n['unit'],
                        'val1': val1,
                        'val2': val2,
                        'pct1': pct1,
                        'pct2': pct2,
                        'winner': winner,
                    })
                
                # Generate insight messages
                if food1.iron_mg > food2.iron_mg * 1.5:
                    messages.append(f"🔴 {food1.food_name[:30]} has {food1.iron_mg:.1f}mg iron — more than {food2.food_name[:30]}")
                elif food2.iron_mg > food1.iron_mg * 1.5:
                    messages.append(f"🔴 {food2.food_name[:30]} has {food2.iron_mg:.1f}mg iron — more than {food1.food_name[:30]}")
                
                if food1.fiber_g > food2.fiber_g * 1.5:
                    messages.append(f"🌾 {food1.food_name[:30]} has {food1.fiber_g:.1f}g fiber — better for digestion")
                elif food2.fiber_g > food1.fiber_g * 1.5:
                    messages.append(f"🌾 {food2.food_name[:30]} has {food2.fiber_g:.1f}g fiber — better for digestion")
                
                if not messages:
                    messages.append("💡 These foods have similar nutritional profiles.")
                
                # ===== ADD THIS RIGHT HERE =====
                # AJAX response for popup
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'food1': {'name': food1.food_name, 'id': food1.id},
                        'food2': {'name': food2.food_name, 'id': food2.id},
                        'comparison': comparison,
                        'messages': messages,
                    })
                # ===== END OF ADDED CODE =====
                
            except Food.DoesNotExist:
                pass

            except Food.DoesNotExist:
                pass
    
    return render(request, 'foods/compare.html', {
        'foods': foods,
        'food1': food1,
        'food2': food2,
        'comparison': comparison,
        'messages': messages,
    })

def get_units(request):
    """Return available units for a food as JSON"""
    food_id = request.GET.get('food_id')
    if food_id:
        try:
            units = UnitConversion.objects.filter(food_id=food_id)
            unit_list = [{'name': u.unit_name, 'grams': u.grams} for u in units]
            return JsonResponse({'units': unit_list})
        except:
            return JsonResponse({'units': []})
    return JsonResponse({'units': []})

def test(request):
    return HttpResponse("Server is reachable!")
# ===== API ENDPOINTS =====
def api_foods(request):
    """Return all foods as JSON (for developers)"""
    foods = Food.objects.all().values(
        'id', 'food_name', 'category__name', 
        'energy_kcal', 'protein_g', 'fat_g', 'carbohydrate_g', 
        'fiber_g', 'iron_mg', 'calcium_mg', 'vitamin_a_rae_ug'
    )[:50]  # Limit to 50 for performance
    return JsonResponse(list(foods), safe=False)

def api_food_detail(request, food_id):
    """Return a single food with all nutrients as JSON"""
    try:
        food = Food.objects.get(id=food_id)
        data = {
            'id': food.id,
            'name': food.food_name,
            'category': food.category.name,
            'kfct_code': food.kfct_code,
            'energy_kcal': food.energy_kcal,
            'protein_g': food.protein_g,
            'fat_g': food.fat_g,
            'carbohydrate_g': food.carbohydrate_g,
            'fiber_g': food.fiber_g,
            'water_g': food.water_g,
            'iron_mg': food.iron_mg,
            'calcium_mg': food.calcium_mg,
            'magnesium_mg': food.magnesium_mg,
            'phosphorus_mg': food.phosphorus_mg,
            'potassium_mg': food.potassium_mg,
            'sodium_mg': food.sodium_mg,
            'zinc_mg': food.zinc_mg,
            'vitamin_a_rae_ug': food.vitamin_a_rae_ug,
            'thiamin_mg': food.thiamin_mg,
            'riboflavin_mg': food.riboflavin_mg,
            'niacin_mg': food.niacin_mg,
            'vitamin_b6_mg': food.vitamin_b6_mg,
            'folate_ug': food.folate_ug,
            'vitamin_b12_ug': food.vitamin_b12_ug,
            'vitamin_c_mg': food.vitamin_c_mg,
        }
        return JsonResponse(data)
    except Food.DoesNotExist:
        return JsonResponse({'error': 'Food not found'}, status=404)

def api_search(request):
    """Search foods by name"""
    query = request.GET.get('q', '')
    if query:
        foods = Food.objects.filter(food_name__icontains=query).values(
            'id', 'food_name', 'category__name', 'energy_kcal', 'protein_g', 'iron_mg'
        )[:20]
        return JsonResponse(list(foods), safe=False)
    return JsonResponse([], safe=False)

def api_categories(request):
    """Return all categories with food counts"""
    from django.db import models
    categories = Category.objects.annotate(food_count=models.Count('foods')).values(
        'id', 'name', 'food_count'
    )
    return JsonResponse(list(categories), safe=False)

def create_admin(request):
    """Emergency: Create admin user by visiting a URL"""
    from django.contrib.auth.models import User
    
    username = 'admin123'
    email = 'admin@example.com'
    password = 'admin123'
    
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        return HttpResponse(f"✅ Admin user created! Username: {username}, Password: {password}")
    else:
        return HttpResponse(f"⚠️ User '{username}' already exists. Try logging in.")

# ========== HEALTH CHECK ==========
@csrf_exempt
def health_check(request):
    """Health check endpoint for Render"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected'
    })
