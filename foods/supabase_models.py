from django.conf import settings

def get_all_foods():
    """Get all foods from Supabase"""
    try:
        response = settings.supabase.table('foods').select('*').execute()
        return response.data
    except Exception as e:
        print(f"Supabase error in get_all_foods: {e}")
        return []

def get_food_by_id(food_id):
    """Get a single food by ID"""
    try:
        response = settings.supabase.table('foods').select('*').eq('id', food_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Supabase error in get_food_by_id: {e}")
        return None

def search_foods_supabase(query):
    """Search foods by name"""
    try:
        response = settings.supabase.table('foods').select('*').ilike('food_name', f'%{query}%').limit(50).execute()
        return response.data
    except Exception as e:
        print(f"Supabase error in search_foods: {e}")
        return []