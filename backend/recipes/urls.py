from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    TagViewSet,
    IngredientViewSet,
    RecipeViewSet,
    ShoppingCartViewSet,
)

router = DefaultRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('recipes', ShoppingCartViewSet, basename='shopping_cart')

app_name = 'recipes'

urlpatterns = [
    path('', include(router.urls)),
]