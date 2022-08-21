from django.urls import include, path
from djoser.views import TokenDestroyView
from rest_framework.routers import DefaultRouter

from .views import TokenCreateWithCheckBlockStatusView, UserSubscribeViewSet

router = DefaultRouter()
router.register('users', UserSubscribeViewSet, basename='users')

authorization = [
    path(
        'token/login/',
        TokenCreateWithCheckBlockStatusView.as_view(),
        name='login',
    ),
    path('token/logout/', TokenDestroyView.as_view(), name='logout'),
]

app_name = 'users'

urlpatterns = [
    path('auth/', include(authorization)),
    path('', include(router.urls)),
]
