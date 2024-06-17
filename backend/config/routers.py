from rest_framework.routers import DefaultRouter

from apps.content.api.viewsets import (AboutViewSet, BannerViewSet,
                                       ContactViewSet, DeliveryMethodViewSet,
                                       DocumentsViewSet, FAQViewSet,
                                       ReturnConditionsViewSet)
from apps.market.api.viewsets import (BasketViewSet, BrandViewSet,
                                      CategoryViewSet, FavoriteProductsViewSet,
                                      ItemBasketViewSet, OrderViewSet,
                                      ProductViewSet, TagViewSet,
                                      VariantViewSet)
from apps.shipping_and_payment.api.viewsets import ProviderViewSet
from apps.user.api.viewsets import UserViewSet

router = DefaultRouter()
router.register("users", UserViewSet)
router.register("banners", BannerViewSet)
router.register("category", CategoryViewSet)
router.register("products", ProductViewSet)
router.register("tags", TagViewSet)
router.register("contacts", ContactViewSet)
router.register("about", AboutViewSet)
router.register("documents", DocumentsViewSet)
router.register("brands", BrandViewSet)
router.register("basket", BasketViewSet)
router.register('orders', OrderViewSet)
router.register("item_basket", ItemBasketViewSet)
router.register("variants", VariantViewSet)
router.register("FAQ", FAQViewSet)
router.register("delivery_methods", DeliveryMethodViewSet)
router.register('provider', ProviderViewSet)
router.register('favorites', FavoriteProductsViewSet, basename='favorites')
router.register('return_conditions', ReturnConditionsViewSet)
