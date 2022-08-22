from django.db import IntegrityError
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST
)
from rest_framework.viewsets import ModelViewSet

from common.pagination import LimitPageNumberPagination
from common.serializers import RecipeShortReadSerializer
from .filters import IngredientSearchFilter, RecipeFilter
from .mixins import ListRetriveViewSet
from .models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag
)
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    TagSerializer
)


class TagViewSet(ListRetriveViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    http_method_names = ('get',)


class IngredientViewSet(ListRetriveViewSet):
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientSearchFilter
    queryset = Ingredient.objects.all()
    http_method_names = ('get',)


class ShoppingCartViewSet(ModelViewSet):
    queryset = ShoppingCart.objects.all()
    serializer_class = RecipeShortReadSerializer
    permission_classes = (IsAuthenticated,)

    @action(methods=('post', 'delete',), detail=True)
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        shopping_cart, *_ = ShoppingCart.objects.get_or_create(user=request.user)
        if request.method == 'DELETE':
            if not shopping_cart.recipes.filter(pk__in=(recipe.pk,)).exists():
                return Response(
                    {'error': 'Нельзя удалить рецепт, которого нет в списке покупок!'},
                    status=HTTP_400_BAD_REQUEST,
                )
            shopping_cart.recipes.remove(recipe)
            return Response(
                status=HTTP_204_NO_CONTENT,
            )
        if shopping_cart.recipes.filter(pk__in=(recipe.pk,)).exists():
            return Response(
                {'error': 'Рецепт уже добавлен!'},
                status=HTTP_400_BAD_REQUEST,
            )
        shopping_cart.recipes.add(recipe)
        serializer = self.get_serializer(recipe)
        return Response(
            serializer.data,
            status=HTTP_201_CREATED,
        )


class RecipeViewSet(ModelViewSet):
    pagination_class = LimitPageNumberPagination
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    queryset = Recipe.objects.all()
    http_method_names = ('get', 'post', 'put', 'patch', 'delete',)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        serializer = RecipeReadSerializer(
            instance=serializer.instance,
            context={'request': self.request}
        )
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        serializer = RecipeReadSerializer(
            instance=serializer.instance,
            context={'request': self.request},
        )
        return Response(
            serializer.data, status=HTTP_200_OK
        )

    def _add_to_favorite(self, request, recipe):
        try:
            Favorite.objects.create(user=request.user, recipe=recipe)
        except IntegrityError:
            return Response(
                {'error': 'Уже в избранном!'},
                status=HTTP_400_BAD_REQUEST,
            )
        serializer = RecipeShortReadSerializer(recipe)
        return Response(
            serializer.data,
            status=HTTP_201_CREATED,
        )

    def _delete_from_favorite(self, request, recipe):
        favorite = Favorite.objects.filter(user=request.user, recipe=recipe)
        if not favorite.exists():
            return Response(
                {'error': 'Избранного не существует!'},
                status=HTTP_400_BAD_REQUEST,
            )
        favorite.delete()
        return Response(status=HTTP_204_NO_CONTENT)

    @action(
        methods=('post', 'delete',),
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            return self._add_to_favorite(request, recipe)
        return self._delete_from_favorite(request, recipe)

    @action(
        detail=False,
        queryset=ShoppingCart.objects.all(),
        serializer_class=RecipeShortReadSerializer,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        try:
            recipes = (
                request.user.shopping_cart.recipes.prefetch_related('ingredients')
            )
            ingredients = (
                recipes.order_by('ingredients__ingredient__name').values(
                    'ingredients__ingredient__name',
                    'ingredients__ingredient__measurement_unit'
                ).annotate(
                    total=Sum('ingredients__amount')
                )
            )
        except ShoppingCart.DoesNotExist:
            return Response(
                {'error': 'У вас нет списка покупок!'},
                status=HTTP_400_BAD_REQUEST
            )
        content = 'Список необходимых продуктов:\n'
        for i, ingredient in enumerate(ingredients, start=1):
            content += (
                f'{i}) {ingredient["ingredients__ingredient__name"]} '
                f' — {ingredient["total"]}'
                f' {ingredient["ingredients__ingredient__measurement_unit"]}\r\n'
            )
        response = HttpResponse(
            content, content_type='text/plain,charset=utf8'
        )
        response['Content-Disposition'] = f'attachment; filename=shopping_cart.txt'
        return response
