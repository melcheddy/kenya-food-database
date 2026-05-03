from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

def home(request):
    return HttpResponse("""
    <h1>🇰🇪 Kenya Food Database</h1>
    <p>Django is running on Vercel!</p>
    <p>✅ Server is working</p>
    <p><a href="/test/">Test endpoint</a></p>
    <p><a href="/health/">Health check</a></p>
    """)

def test(request):
    return HttpResponse("✅ Django is working on Vercel!")

def health_check(request):
    return JsonResponse({"status": "healthy", "message": "Server is running"})

def search_foods(request):
    return JsonResponse({"message": "Search endpoint - coming soon"})

def food_detail(request, food_id):
    return JsonResponse({"message": f"Food detail for ID {food_id} - coming soon"})

def nutrient_calculator(request):
    return JsonResponse({"message": "Nutrient calculator - coming soon"})

def recall_24hr(request):
    return JsonResponse({"message": "24hr recall - coming soon"})

def compare_foods(request):
    return JsonResponse({"message": "Compare foods - coming soon"})

def get_units(request):
    return JsonResponse({"units": []})

def export_food_excel(request, food_id):
    return HttpResponse("Excel export - coming soon")

def export_recall_excel(request):
    return HttpResponse("Excel export - coming soon")

def api_foods(request):
    return JsonResponse([], safe=False)

def api_food_detail(request, food_id):
    return JsonResponse({})

def api_search(request):
    return JsonResponse([])

def api_categories(request):
    return JsonResponse([])

def create_admin(request):
    return HttpResponse("Admin creation disabled")