from django.contrib.admin import ModelAdmin, display, register
from django.db.models import Count, Sum

from .models import (
    CountOfIngredient,
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag
)


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('id', 'name', 'slug', 'color',)
    search_fields = ('name', 'slug',)
    ordering = ('color',)


@register(CountOfIngredient)
class CountOfIngredientAdmin(ModelAdmin):
    list_display = (
        'id', 'ingredient', 'amount', 'get_measurement_unit',
        'get_recipes_count',
    )
    readonly_fields = ('get_measurement_unit',)
    list_filter = ('ingredient',)
    ordering = ('ingredient',)

    @display(description='Единица измерения')
    def get_measurement_unit(self, obj):
        try:
            return obj.ingredient.measurement_unit
        except CountOfIngredient.ingredient.RelatedObjectDoesNotExist:
            return 'Пусто'

    @display(description='Количество ссылок в рецептах')
    def get_recipes_count(self, obj):
        return obj.recipes.count()


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = ('name', 'author',)
    list_filter = ('name', 'author', 'tags',)
    readonly_fields = ('added_in_favorites',)

    @display(description='Общее число добавлений в избранное')
    def added_in_favorites(self, obj):
        return obj.favorites.count()


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)
    search_fields = ('name',)
    ordering = ('measurement_unit',)


@register(Favorite)
class FavoriteAdmin(ModelAdmin):
    list_display = ('user', 'recipe',)
    list_filter = ('user', 'recipe',)


@register(ShoppingCart)
class ShoppingCartAdmin(ModelAdmin):
    list_display = ('user', 'count_ingredients',)
    readonly_fields = ('count_ingredients',)

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    @display(description='Количество ингредиентов')
    def count_ingredients(self, obj):
        return (
            obj.recipes.annotate(count_ingredients=Count('ingredients')).all()
            .aggregate(total=Sum('count_ingredients'))['total']
        )
