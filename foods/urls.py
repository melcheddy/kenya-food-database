from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search_foods, name='search'),
    path('food/<int:food_id>/', views.food_detail, name='food_detail'),
    path('calculator/', views.nutrient_calculator, name='calculator'),
    path('recall/', views.recall_24hr, name='recall'),
    path('compare/', views.compare_foods, name='compare'),
    path('test/', views.test),
    path('get-units/', views.get_units, name='get_units'),
        # API Endpoints
    path('api/foods/', views.api_foods, name='api_foods'),
    path('api/food/<int:food_id>/', views.api_food_detail, name='api_food_detail'),
    path('api/search/', views.api_search, name='api_search'),
    path('api/categories/', views.api_categories, name='api_categories'),
    path('create-admin/', views.create_admin, name='create_admin'),
]