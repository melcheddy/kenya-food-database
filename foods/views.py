from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from .models import Food, Category, RDA, UnitConversion
from .swap_suggestions import SWAP_SUGGESTIONS, NUTRIENT_SWAPS, get_cost_tag

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
    
    # Detect if user is budget-conscious
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
    
    # Get cost of current food
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
    
    if request.method == 'POST':
        food_id = request.POST.get('food_id')
        
        # Handle no food selected (Change button)
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
            
            # Convert to grams
            grams = amount
            if unit != 'grams':
                try:
                    conversion = UnitConversion.objects.get(food=food_selected, unit_name=unit)
                    grams = amount * conversion.grams
                except UnitConversion.DoesNotExist:
                    grams = amount
            
            # Calculate nutrients — THIS IS YOUR RESULT DICTIONARY
            result = {
                'food_name': food_selected.food_name,
                'amount': amount,
                'unit': unit,
                'grams': grams,
                # Proximates
                'energy_kcal': (grams / 100) * food_selected.energy_kcal,
                'protein_g': (grams / 100) * food_selected.protein_g,
                'fat_g': (grams / 100) * food_selected.fat_g,
                'carbohydrate_g': (grams / 100) * food_selected.carbohydrate_g,
                'fiber_g': (grams / 100) * food_selected.fiber_g,
                'water_g': (grams / 100) * food_selected.water_g,
                # Minerals
                'iron_mg': (grams / 100) * food_selected.iron_mg,
                'calcium_mg': (grams / 100) * food_selected.calcium_mg,
                'magnesium_mg': (grams / 100) * food_selected.magnesium_mg,
                'phosphorus_mg': (grams / 100) * food_selected.phosphorus_mg,
                'potassium_mg': (grams / 100) * food_selected.potassium_mg,
                'sodium_mg': (grams / 100) * food_selected.sodium_mg,
                'zinc_mg': (grams / 100) * food_selected.zinc_mg,
                # Vitamins
                'vitamin_a_rae_ug': (grams / 100) * food_selected.vitamin_a_rae_ug,
                'thiamin_mg': (grams / 100) * food_selected.thiamin_mg,
                'riboflavin_mg': (grams / 100) * food_selected.riboflavin_mg,
                'niacin_mg': (grams / 100) * food_selected.niacin_mg,
                'vitamin_b6_mg': (grams / 100) * food_selected.vitamin_b6_mg,
                'folate_ug': (grams / 100) * food_selected.folate_ug,
                'vitamin_b12_ug': (grams / 100) * food_selected.vitamin_b12_ug,
                'vitamin_c_mg': (grams / 100) * food_selected.vitamin_c_mg,
            }
            
            # Get RDA based on age and gender
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
            
        except Food.DoesNotExist:
            pass
    
    # Prepare AJAX response if needed
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'result': result,
            'rda': rda,
        })
    
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
        total_vitamin_a = 0
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
                        
                        total_energy += (grams / 100) * food.energy_kcal
                        total_protein += (grams / 100) * food.protein_g
                        total_iron += (grams / 100) * food.iron_mg
                        total_fiber += (grams / 100) * food.fiber_g
                        total_calcium += (grams / 100) * food.calcium_mg
                        total_vitamin_a += (grams / 100) * food.vitamin_a_rae_ug
                        total_fluid_ml += (grams / 100) * food.water_g
                        
                    except (Food.DoesNotExist, ValueError):
                        pass
        
        # Hydration AI
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
        
        # Prepare results
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
        
        # Hydration message
        if fluid_percent < 80:
            results['hydration_message'] = '⚠️ You might be running low on fluids. Try to drink more water throughout the day.'
        elif fluid_percent <= 120:
            results['hydration_message'] = '✅ Great job! Your hydration is on point.'
        else:
            results['hydration_message'] = '💧 You\'re well hydrated!'
        
        # ===== RDI ANALYSIS =====
        if gender == 'female':
            if age < 19:
                rdi = {
                    'energy_kcal': 2000,
                    'protein_g': 46,
                    'iron_mg': 15,
                    'calcium_mg': 1300,
                    'vitamin_a_rae_ug': 600,
                    'vitamin_c_mg': 45,
                    'fiber_g': 25,
                }
            else:
                rdi = {
                    'energy_kcal': 2100,
                    'protein_g': 46,
                    'iron_mg': 29,
                    'calcium_mg': 1000,
                    'vitamin_a_rae_ug': 500,
                    'vitamin_c_mg': 45,
                    'fiber_g': 25,
                }
        else:
            if age < 19:
                rdi = {
                    'energy_kcal': 2400,
                    'protein_g': 52,
                    'iron_mg': 11,
                    'calcium_mg': 1300,
                    'vitamin_a_rae_ug': 700,
                    'vitamin_c_mg': 45,
                    'fiber_g': 31,
                }
            else:
                rdi = {
                    'energy_kcal': 2500,
                    'protein_g': 56,
                    'iron_mg': 11,
                    'calcium_mg': 1000,
                    'vitamin_a_rae_ug': 600,
                    'vitamin_c_mg': 45,
                    'fiber_g': 30,
                }
        
        # Calculate percentages
        rdi_percentages = {
            'energy_percent': (total_energy / rdi['energy_kcal']) * 100 if rdi['energy_kcal'] > 0 else 0,
            'protein_percent': (total_protein / rdi['protein_g']) * 100 if rdi['protein_g'] > 0 else 0,
            'iron_percent': (total_iron / rdi['iron_mg']) * 100 if rdi['iron_mg'] > 0 else 0,
            'calcium_percent': (total_calcium / rdi['calcium_mg']) * 100 if rdi['calcium_mg'] > 0 else 0,
        }
        
        results['rdi'] = rdi
        results['rdi_percentages'] = rdi_percentages
        
        # Status messages
        results['status_messages'] = []
        
        if rdi_percentages['iron_percent'] < 70:
            results['status_messages'].append({
                'nutrient': 'Iron',
                'status': 'low',
                'message': f"⚠️ Your iron intake ({total_iron:.1f}mg) is only {rdi_percentages['iron_percent']:.0f}% of daily needs.",
                'suggestions': ['sukuma wiki', 'beans', 'dagaa omena', 'whole maize flour']
            })
        elif rdi_percentages['iron_percent'] > 130:
            results['status_messages'].append({
                'nutrient': 'Iron',
                'status': 'high',
                'message': f"✅ Your iron intake ({total_iron:.1f}mg) is good at {rdi_percentages['iron_percent']:.0f}% of daily needs."
            })
        else:
            results['status_messages'].append({
                'nutrient': 'Iron',
                'status': 'good',
                'message': f"✅ Your iron intake ({total_iron:.1f}mg) meets {rdi_percentages['iron_percent']:.0f}% of daily needs."
            })
        
        if rdi_percentages['protein_percent'] < 70:
            results['status_messages'].append({
                'nutrient': 'Protein',
                'status': 'low',
                'message': f"⚠️ Your protein intake ({total_protein:.1f}g) is only {rdi_percentages['protein_percent']:.0f}% of daily needs.",
                'suggestions': ['beans', 'eggs', 'chicken', 'fish']
            })
        else:
            results['status_messages'].append({
                'nutrient': 'Protein',
                'status': 'good',
                'message': f"✅ Your protein intake ({total_protein:.1f}g) meets {rdi_percentages['protein_percent']:.0f}% of daily needs."
            })
        
        if rdi_percentages['energy_percent'] < 70:
            results['status_messages'].append({
                'nutrient': 'Energy',
                'status': 'low',
                'message': f"⚠️ Your energy intake ({total_energy:.0f}kcal) is only {rdi_percentages['energy_percent']:.0f}% of daily needs.",
                'suggestions': ['ugali', 'rice', 'chapati', 'sweet potato']
            })
        elif rdi_percentages['energy_percent'] > 130:
            results['status_messages'].append({
                'nutrient': 'Energy',
                'status': 'high',
                'message': f"⚠️ Your energy intake ({total_energy:.0f}kcal) is {rdi_percentages['energy_percent']:.0f}% of daily needs — you may be overeating."
            })
        else:
            results['status_messages'].append({
                'nutrient': 'Energy',
                'status': 'good',
                'message': f"✅ Your energy intake ({total_energy:.0f}kcal) meets {rdi_percentages['energy_percent']:.0f}% of daily needs."
            })

    # After calculating results, if AJAX request, return JSON
if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
    return JsonResponse({
        'success': True,
        'results': results,
        'name': name or 'there',  # Personalized greeting
    })

    return render(request, 'foods/recall_24hr.html', {
        'foods': foods,
        'meals': meals,
        'results': results,
    })

def compare_foods(request):
    import traceback
    try:
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
                        {'name': 'Vitamin A (µg)', 'key': 'vitamin_a_rae_ug', 'unit': 'µg', 'higher_is': 'better'},
                        {'name': 'Vitamin C (mg)', 'key': 'vitamin_c_mg', 'unit': 'mg', 'higher_is': 'better'},
                        {'name': 'Zinc (mg)', 'key': 'zinc_mg', 'unit': 'mg', 'higher_is': 'better'},
                    ]
                    
                    comparison = []
                    for n in nutrients:
                        val1 = getattr(food1, n['key'], 0)
                        val2 = getattr(food2, n['key'], 0)
                        
                        if n['higher_is'] == 'better':
                            if val1 > val2:
                                winner = 1
                            elif val2 > val1:
                                winner = 2
                            else:
                                winner = 0
                        else:
                            winner = 0
                        
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
                    
                    if food1.iron_mg > food2.iron_mg * 1.5:
                        messages.append(f"🔴 {food1.food_name[:30]} has {food1.iron_mg:.1f}mg iron — more than {food2.food_name[:30]}")
                    elif food2.iron_mg > food1.iron_mg * 1.5:
                        messages.append(f"🔴 {food2.food_name[:30]} has {food2.iron_mg:.1f}mg iron — more than {food1.food_name[:30]}")
                    
                    if not messages:
                        messages.append("💡 These foods have similar nutritional profiles.")
                    
                    # AJAX response
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'food1': {'name': food1.food_name, 'id': food1.id},
                            'food2': {'name': food2.food_name, 'id': food2.id},
                            'comparison': comparison,
                            'messages': messages,
                        })
                    
                except Food.DoesNotExist:
                    pass
        
        return render(request, 'foods/compare.html', {
            'foods': foods,
            'food1': food1,
            'food2': food2,
            'comparison': comparison,
            'messages': messages,
        })
    
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