from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from .models import Food, Category, RDA, UnitConversion
from .swap_suggestions import SWAP_SUGGESTIONS, NUTRIENT_SWAPS, get_cost_tag

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

def health_check(request):
    return HttpResponse("OK")