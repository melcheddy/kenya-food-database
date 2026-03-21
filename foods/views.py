from django.shortcuts import render
from .models import Food, Category, RDA, UnitConversion
from .swap_suggestions import SWAP_SUGGESTIONS, NUTRIENT_SWAPS, get_cost_tag
from django.http import JsonResponse

def home(request):
    """Homepage with search"""
    return render(request, 'foods/home.html')

def search_foods(request):
    """Search for foods by name"""
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    
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
    food = Food.objects.get(id=food_id)

    if 'viewed_foods' not in request.session:
        request.session['viewed_foods'] = []
    
    viewed = request.session['viewed_foods']
    viewed.append(food.food_name)
    request.session['viewed_foods'] = viewed[-10:]
    # Step 2: Detect if user is budget-conscious
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
    
    # ... rest of your function ...
    
    # Get cost of current food
    from .swap_suggestions import get_cost_tag
    current_cost = get_cost_tag(food.food_name)
    
    swap_suggestions = []
    food_name_lower = food.food_name.lower()
    
    # Check for direct swaps
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
    
    # Add cost-aware suggestions for high-cost foods
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
    
    # Check for nutrient-based swaps
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
def nutrient_calculator(request):
    """Calculate nutrients based on food and amount with unit conversion"""
    foods = Food.objects.all().order_by('food_name')
    categories = Category.objects.all()
    rdas = RDA.objects.all()
    
    result = None
    food_selected = None
    amount = 100
    unit = 'grams'
    gender = 'female'
    age = 30
    available_units = []
    
    if request.method == 'POST':
        food_id = request.POST.get('food_id')
        amount = float(request.POST.get('amount', 100))
        unit = request.POST.get('unit', 'grams')
        gender = request.POST.get('gender', 'female')
        age = int(request.POST.get('age', 30))
        
        try:
            food_selected = Food.objects.get(id=food_id)
            
            # Get available units for this food
            available_units = UnitConversion.objects.filter(food=food_selected)
            
            # Convert to grams if unit is not 'grams'
            grams = amount
            if unit != 'grams':
                try:
                    conversion = UnitConversion.objects.get(
                        food=food_selected,
                        unit_name=unit
                    )
                    grams = amount * conversion.grams
                except UnitConversion.DoesNotExist:
                    grams = amount
            
            # Calculate nutrients based on grams
            result = {
                'food': food_selected,
                'amount': amount,
                'unit': unit,
                'grams': grams,
                'energy_kcal': (grams / 100) * food_selected.energy_kcal,
                'protein_g': (grams / 100) * food_selected.protein_g,
                'fat_g': (grams / 100) * food_selected.fat_g,
                'carbohydrate_g': (grams / 100) * food_selected.carbohydrate_g,
                'fiber_g': (grams / 100) * food_selected.fiber_g,
                'iron_mg': (grams / 100) * food_selected.iron_mg,
                'calcium_mg': (grams / 100) * food_selected.calcium_mg,
                'vitamin_a_rae_ug': (grams / 100) * food_selected.vitamin_a_rae_ug,
                'folate_ug': (grams / 100) * food_selected.folate_ug,
                'vitamin_c_mg': (grams / 100) * food_selected.vitamin_c_mg,
                'zinc_mg': (grams / 100) * food_selected.zinc_mg,
            }
            
            # Find appropriate RDA based on gender and age
            if age < 1:
                life_stage = 'infant'
            elif age < 4:
                life_stage = 'child_1_3'
            elif age < 9:
                life_stage = 'child_4_8'
            elif age < 14:
                life_stage = 'child_9_13'
            elif age < 19:
                life_stage = 'adolescent_14_18'
            else:
                life_stage = 'adult'
            
            # For adults, we need to check age ranges
            if life_stage == 'adult':
                # First try to find exact age match
                rda_entry = RDA.objects.filter(
                    gender=gender,
                    life_stage='adult',
                    age_min__lte=age,
                    age_max__gte=age
                ).first()
                
                # If no exact match, try to get any adult entry (fallback)
                if not rda_entry:
                    rda_entry = RDA.objects.filter(
                        gender=gender,
                        life_stage='adult'
                    ).first()
            else:
                # For non-adults, just filter by life stage
                rda_entry = RDA.objects.filter(
                    gender=gender,
                    life_stage=life_stage
                ).first()
            
            # Add percentage calculations
            if result and rda_entry:
                result['energy_percent'] = (result['energy_kcal'] / rda_entry.energy_kcal) * 100
                result['iron_percent'] = (result['iron_mg'] / rda_entry.iron_mg) * 100 if rda_entry.iron_mg > 0 else 0
                result['protein_percent'] = (result['protein_g'] / rda_entry.protein_g) * 100 if rda_entry.protein_g > 0 else 0
            
            result['rda'] = rda_entry
            
        except Food.DoesNotExist:
            pass
    
    return render(request, 'foods/calculator.html', {
        'foods': foods,
        'categories': categories,
        'result': result,
        'food_selected': food_selected,
        'amount': amount,
        'unit': unit,
        'gender': gender,
        'age': age,
        'available_units': available_units,
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
        # Get user info
        name = request.POST.get('name', '')
        age = request.POST.get('age', '')
        gender = request.POST.get('gender', 'female')
        
        # Initialize totals
        total_energy = 0
        total_protein = 0
        total_iron = 0
        total_fiber = 0
        total_calcium = 0
        total_vitamin_a = 0  # ADD THIS
        total_fluid_ml = 0

        
        # Convert age to int if provided
        try:
            age = int(age) if age else 30
        except ValueError:
            age = 30
        
        # Process fluids first
        fluid_ids = request.POST.getlist('fluid_id[]')
        fluid_amounts = request.POST.getlist('fluid_amount[]')
        fluid_units = request.POST.getlist('fluid_unit[]')
        
        for i in range(len(fluid_ids)):
            if fluid_ids[i] and fluid_amounts[i]:
                try:
                    amount = float(fluid_amounts[i])
                    unit = fluid_units[i]
                    
                    # Convert to ml
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
        
        # Process foods from all meals
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
                        
                        # Convert to grams
                        grams = amount
                        if unit != 'grams':
                            try:
                                conversion = UnitConversion.objects.get(
                                    food=food,
                                    unit_name=unit
                                )
                                grams = amount * conversion.grams
                            except UnitConversion.DoesNotExist:
                                grams = amount
                        
                        # Add to nutrient totals
                        total_energy += (grams / 100) * food.energy_kcal
                        total_protein += (grams / 100) * food.protein_g
                        total_iron += (grams / 100) * food.iron_mg
                        
                        # Add water from food (1g water = 1ml)
                        total_fluid_ml += (grams / 100) * food.water_g
                        
                    except (Food.DoesNotExist, ValueError):
                        pass
        
        # Calculate Adequate Intake (AI) for water based on age and gender
        if age < 4:
            ai_liters = 1.3  # 1-3 years
        elif age < 9:
            ai_liters = 1.7  # 4-8 years
        elif age < 14:
            ai_liters = 2.4 if gender == 'male' else 2.1  # 9-13 years
        elif age < 19:
            ai_liters = 3.3 if gender == 'male' else 2.3  # 14-18 years
        else:
            if gender == 'male':
                ai_liters = 3.7  # Adult male
            else:
                ai_liters = 2.7  # Adult female
        
        total_fluid_l = total_fluid_ml / 1000
        fluid_percent = (total_fluid_l / ai_liters) * 100 if ai_liters > 0 else 0
        
        # Prepare results
        results = {
            'total_energy': total_energy,
            'total_protein': total_protein,
            'total_iron': total_iron,
            'total_fluid_ml': total_fluid_ml,
            'total_fluid_l': total_fluid_l,
            'ai_liters': ai_liters,
            'fluid_percent': fluid_percent,
            'name': name,
            'age': age,
            'gender': gender,
        }
        
        # Add hydration message
        if fluid_percent < 80:
            results['hydration_message'] = '⚠️ You might be running low on fluids. Try to drink more water throughout the day.'
            results['hydration_class'] = 'warning'
        elif fluid_percent <= 120:
            results['hydration_message'] = '✅ Great job! Your hydration is on point.'
            results['hydration_class'] = 'good'
        else:
            results['hydration_message'] = '💧 You\'re well hydrated! Remember that water also comes from the foods you eat.'
            results['hydration_class'] = 'info'
    # ===== ADD IMPROVEMENT SUGGESTIONS =====
        improvements = []
        
        # Check iron deficiency
        if gender == 'female':
            iron_target = 29
        else:
            iron_target = 11
        
        if total_iron < iron_target * 0.7:
            improvements.append({
                'nutrient': 'Iron',
                'current': total_iron,
                'target': iron_target,
                'suggestions': [
                    ('sukuma wiki', 'Rich in iron and vitamin C'),
                    ('beans', 'Excellent plant-based iron source'),
                    ('dagaa omena', 'Calcium + iron from small fish'),
                ]
            })
        
        # Check protein deficiency
        if gender == 'female':
            protein_target = 46
        else:
            protein_target = 56
        
        if total_protein < protein_target * 0.7:
            improvements.append({
                'nutrient': 'Protein',
                'current': total_protein,
                'target': protein_target,
                'suggestions': [
                    ('beans', 'Affordable plant protein'),
                    ('eggs', 'Complete protein, easy to add'),
                    ('dagaa', 'High protein, low cost'),
                ]
            })
        
        # Check fiber deficiency
        fiber_target = 25
        if total_fiber < fiber_target * 0.7:
            improvements.append({
                'nutrient': 'Fiber',
                'current': total_fiber,
                'target': fiber_target,
                'suggestions': [
                    ('whole maize flour', 'Swap refined for whole'),
                    ('beans', 'Add to meals for fiber'),
                    ('sukuma wiki', 'Vegetables add fiber'),
                ]
            })
        
        # Check calcium deficiency
        calcium_target = 1000
        if total_calcium < calcium_target * 0.7:
            improvements.append({
                'nutrient': 'Calcium',
                'current': total_calcium,
                'target': calcium_target,
                'suggestions': [
                    ('milk', 'Fresh or fermented (mursik)'),
                    ('dagaa omena', 'Calcium from bones'),
                    ('amaranth leaves', 'Terere is calcium-rich'),
                ]
            })
        
        # Check vitamin A deficiency
        if gender == 'female':
            vita_target = 500
        else:
            vita_target = 600
        
        if total_vitamin_a < vita_target * 0.7:
            improvements.append({
                'nutrient': 'Vitamin A',
                'current': total_vitamin_a,
                'target': vita_target,
                'suggestions': [
                    ('sukuma wiki', 'Rich in vitamin A'),
                    ('sweet potato orange', 'High in vitamin A'),
                    ('mango', 'Good source of vitamin A'),
                    ('pawpaw', 'Vitamin A + digestive enzymes'),
                ]
            })
        
        # Add improvements to results
        results['improvements'] = improvements
    
    return render(request, 'foods/recall_24hr.html', {
        'foods': foods,
        'meals': meals,
        'results': results,
    })

def compare_foods(request):
    """Compare two foods side by side"""
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
                
                # Prepare comparison data
                nutrients = [
                    {'name': 'Energy (kcal)', 'key': 'energy_kcal', 'unit': 'kcal', 'higher_is': 'better'},
                    {'name': 'Protein (g)', 'key': 'protein_g', 'unit': 'g', 'higher_is': 'better'},
                    {'name': 'Fat (g)', 'key': 'fat_g', 'unit': 'g', 'higher_is': 'neutral'},
                    {'name': 'Carbohydrate (g)', 'key': 'carbohydrate_g', 'unit': 'g', 'higher_is': 'neutral'},
                    {'name': 'Fiber (g)', 'key': 'fiber_g', 'unit': 'g', 'higher_is': 'better'},
                    {'name': 'Iron (mg)', 'key': 'iron_mg', 'unit': 'mg', 'higher_is': 'better'},
                    {'name': 'Calcium (mg)', 'key': 'calcium_mg', 'unit': 'mg', 'higher_is': 'better'},
                    {'name': 'Vitamin A (µg)', 'key': 'vitamin_a_rae_ug', 'unit': 'µg', 'higher_is': 'better'},
                    {'name': 'Vitamin C (mg)', 'key': 'vitamin_c_mg', 'unit': 'mg', 'higher_is': 'better'},
                    {'name': 'Zinc (mg)', 'key': 'zinc_mg', 'unit': 'mg', 'higher_is': 'better'},
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
                
                # Generate behavior change messages
                messages = []
                
                # Iron comparison
                if food1.iron_mg > food2.iron_mg * 1.5 and food2.iron_mg > 0:
                    percent_more = ((food1.iron_mg / food2.iron_mg) - 1) * 100
                    messages.append(f"🔴 {food1.food_name[:30]} has {food1.iron_mg:.1f}mg iron — {percent_more:.0f}% more than {food2.food_name[:30]}")
                elif food2.iron_mg > food1.iron_mg * 1.5 and food1.iron_mg > 0:
                    percent_more = ((food2.iron_mg / food1.iron_mg) - 1) * 100
                    messages.append(f"🔴 {food2.food_name[:30]} has {food2.iron_mg:.1f}mg iron — {percent_more:.0f}% more than {food1.food_name[:30]}")
                
                # Fiber comparison
                if food1.fiber_g > food2.fiber_g * 1.5 and food2.fiber_g > 0:
                    messages.append(f"🌾 {food1.food_name[:30]} has {food1.fiber_g:.1f}g fiber — great for digestion!")
                elif food2.fiber_g > food1.fiber_g * 1.5 and food1.fiber_g > 0:
                    messages.append(f"🌾 {food2.food_name[:30]} has {food2.fiber_g:.1f}g fiber — great for digestion!")
                
                # Protein comparison
                if food1.protein_g > food2.protein_g * 1.5 and food2.protein_g > 0:
                    messages.append(f"🥩 {food1.food_name[:30]} is higher in protein ({food1.protein_g:.1f}g vs {food2.protein_g:.1f}g)")
                elif food2.protein_g > food1.protein_g * 1.5 and food1.protein_g > 0:
                    messages.append(f"🥩 {food2.food_name[:30]} is higher in protein ({food2.protein_g:.1f}g vs {food1.protein_g:.1f}g)")
                
                if not messages:
                    messages.append("💡 These foods have similar nutritional profiles. Consider variety in your diet!")
                
            except Food.DoesNotExist:
                pass
    
def compare_foods(request):
    import traceback
    try:
        except Exception as e:
        print("="*50)
        print("ERROR in compare_foods:")
        traceback.print_exc()
        print("="*50)
        return render(request, 'foods/compare.html', {
            'foods': Food.objects.all().order_by('food_name'),
            'food1': None,
            'food2': None,
            'comparison': None,
            'messages': ['Error loading compare page. Please try again.'],
        })
    # ... all your code ...
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
            from .models import UnitConversion
            units = UnitConversion.objects.filter(food_id=food_id)
            unit_list = [{'name': u.unit_name, 'grams': u.grams} for u in units]
            return JsonResponse({'units': unit_list})
        except:
            return JsonResponse({'units': []})
    return JsonResponse({'units': []})

def test(request):
    return HttpResponse("Server is reachable!")