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
]