"""loyalty_reward URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import url
from django.views.static import serve

from rest_framework.routers import DefaultRouter

from core.views import CustomRefreshTokenView, UserRegisterView, UserViewSet, empty_view, FeatureViewSet, FeatureAccessViewSet
from durian_store.views import CategoryViewSet, ProductViewSet, PromoCodeViewSet, OrderViewSet, SystemSettingViewSet, HomeBannerViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'users', UserViewSet)
router.register(r'features', FeatureViewSet)
router.register(r'feature-accesses', FeatureAccessViewSet)
router.register(r'rest-auth/registration', UserRegisterView, basename='public-user-registration')

router.register(r'durian/categories', CategoryViewSet, basename='durian-category')
router.register(r'durian/products', ProductViewSet, basename='durian-product')
router.register(r'durian/promo-codes', PromoCodeViewSet, basename='durian-promo-code')
router.register(r'durian/orders', OrderViewSet, basename='durian-order')
router.register(r'durian/settings', SystemSettingViewSet, basename='durian-setting')
router.register(r'durian/banners', HomeBannerViewSet, basename='durian-banner')

api_url = 'v1/'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/reset-password/<uidb64>/<token>/',
         empty_view, name='password_reset_confirm'),
    path(api_url, include(router.urls)),
    path(api_url + 'rest-auth/', include('dj_rest_auth.urls')),
    path('rest-auth/registration/', include('dj_rest_auth.registration.urls')),
    url(api_url + 'api-token-refresh/', CustomRefreshTokenView.as_view(), name='token_refresh'),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
