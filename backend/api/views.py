from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponse
from django.db import IntegrityError
from django.db.models import Count, Sum
from djoser.views import TokenCreateView, UserViewSet
from rest_framework.viewsets import ModelViewSet
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

from foodgram.models import Tag, CountOfIngredient, Recipe, Ingredient, User, ShoppingCart, Subscribe, Favorite
from .mixins import ListRetriveViewSet
from .pagination import LimitPageNumberPagination
from .permissions import IsAuthorOrAdminOrReadOnly
from .filters import IngredientSearchFilter, RecipeFilter

from .serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    RecipeShortReadSerializer,
    TagSerializer,
    SubscriptionSerializer,
)


class TagViewSet(ListRetriveViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    http_method_names = ('get',)


class IngredientViewSet(ListRetriveViewSet):
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    queryset = Ingredient.objects.all()
    http_method_names = ('get',)


class TokenCreateWithCheckBlockStatusView(TokenCreateView):
    def _action(self, serializer):
        if serializer.user.is_blocked:
            return Response(
                {'error': 'Аккаунт заблокирован!'},
                status=HTTP_400_BAD_REQUEST,
            )
        return super()._action(serializer)


class UserSubscribeViewSet(UserViewSet):
    pagination_class = LimitPageNumberPagination
    lookup_url_kwarg = 'user_id'

    def get_subscribtion_serializer(self, *args, **kwargs):
        kwargs.setdefault('context', self.get_serializer_context())
        return SubscriptionSerializer(*args, **kwargs)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        queryset = User.objects.filter(subscribing__user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_subscribtion_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_subscribtion_serializer(queryset, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def create_subscribe(self, request, author):
        if request.user == author:
            return Response(
                {'error': 'Нельзя подписаться на себя.'},
                status=HTTP_400_BAD_REQUEST,
            )
        try:
            subscribe = Subscribe.objects.create(
                user=request.user,
                author=author,
            )
        except IntegrityError:
            return Response(
                {'error': 'Нельзя подписаться дважды!'},
                status=HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_subscribtion_serializer(subscribe.author)
        return Response(serializer.data, status=HTTP_201_CREATED)

    def delete_subscribe(self, request, author):
        try:
            Subscribe.objects.get(user=request.user, author=author).delete()
        except Subscribe.DoesNotExist:
            return Response(
                {'error': 'Нельзя отписаться от пользователя, на которого не подписан.'},
                status=HTTP_400_BAD_REQUEST,
            )
        return Response(
            status=HTTP_204_NO_CONTENT
        )

    @action(
        methods=('post', 'delete',),
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, user_id=None):
        try:
            author = get_object_or_404(User, pk=user_id)
        except Http404:
            return Response(
                {'error': 'Пользователь не найден!'},
                status=HTTP_404_NOT_FOUND,
            )
        if request.method == 'POST':
            return self.create_subscribe(request, author)
        return self.delete_subscribe(request, author)


class ShoppingCartViewSet(ModelViewSet):
    queryset = ShoppingCart.objects.all()
    serializer_class = RecipeShortReadSerializer
    permission_classes = (IsAuthenticated,)

    @action(methods=('post', 'delete',), detail=True)
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        shopping_cart = (
            ShoppingCart.objects.get_or_create(user=request.user)[0]
        )
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
        print(serializer.initial_data)
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

    def add_to_favorite(self, request, recipe):
        try:
            Favorite.objects.create(user=request.user, recipe=recipe)
        except IntegrityError:
            return Response(
                {'error': 'Вы уже подписаны!'},
                status=HTTP_400_BAD_REQUEST,
            )
        serializer = RecipeShortReadSerializer(recipe)
        return Response(
            serializer.data,
            status=HTTP_201_CREATED,
        )

    def delete_from_favorite(self, request, recipe):
        favorite = Favorite.objects.filter(user=request.user, recipe=recipe)
        if not favorite.exists():
            return Response(
                {'error': 'Подписки не существует!'},
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
            return self.add_to_favorite(request, recipe)
        return self.delete_from_favorite(request, recipe)

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
                recipes.order_by("ingredients__ingredient__name").values(
                    "ingredients__ingredient__name",
                    "ingredients__ingredient__measurement_unit"
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
        i = 1
        for ingredient in ingredients:
            content += (
                f'{i}) {ingredient["ingredients__ingredient__name"]} '
                f' — {ingredient["total"]}'
                f' {ingredient["ingredients__ingredient__measurement_unit"]}\r\n'
            )
            i += 1
        response = HttpResponse(
            content, content_type='text/plain,charset=utf8'
        )
        response['Content-Disposition'] = f'attachment; filename=shopping_cart.txt'
        return response