import datetime
import logging
import uuid
from typing import Union

import pytz
from django.db.models import (DecimalField, ExpressionWrapper, F, Min, Q,
                              QuerySet, Sum, When)
from django.db.models.functions import Least
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from restdoctor.rest_framework.mixins import (RetrieveModelMixin,
                                              UpdateModelMixin)
from restdoctor.rest_framework.viewsets import (GenericViewSet, ModelViewSet,
                                                ReadOnlyModelViewSet)
from structlog import get_logger

from apps.market.api.filters import ProductOrderingFilter
from apps.market.api.serializers import (BasketSerializer,
                                         BasketUpdateSerializer,
                                         BrandSerializer,
                                         CategoryListSerializer,
                                         CategorySerializer,
                                         FavoriteProductSerializer,
                                         InternalCodeSerializer,
                                         ItemBasketSerializer, OrderSerializer,
                                         PaymentUrlsSerializer,
                                         ProductListSerializer,
                                         ProductSerializer,
                                         SuccessfulPaymentSerializer,
                                         TagSerializer,
                                         TokenInStringSerializer,
                                         UnloggedItemBasketRequestSerializer,
                                         UnloggedItemBasketResponseSerializer,
                                         VariantRequestSerializer,
                                         VariantSerializer)
from apps.market.constants import TINKOFF_CONFIRM_PAYMENT_RESPONSE
from apps.market.enum import BasketStatus, PaymentMethod
from apps.market.logic.facades.basket_facades import  check_order_parameters
from apps.market.logic.facades.tinkoff import basket_payment_url
from apps.market.logic.interactors.basket_interactors import checking__products__to_order, \
    fixed__item_basket__when_accept
from apps.market.logic.interactors.cdek import create_cdek_order, get_cdek_info
from apps.market.logic.interactors.tinkoff import basket_payment_status__change_to_paid

from apps.market.logic.selectors.product_selectors import (
    get_brants__from_products, get_characteristics__from_variants,
    get_price_ranges__from_variants, get_variants__from_products)
from apps.market.models import (Basket, Brand, Category, ItemBasket, Product,
                                Tag, Variant)
from apps.market.tasks import payment_reaction

from apps.user.models import User
from utils.exeption import BusinessLogicException

logger = get_logger(__name__)
cdek_logger = logging.getLogger("cdek")


class BrandViewSet(ReadOnlyModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer

    def get_queryset(self):
        product_ids = Product.objects.get_products_on_display().values_list("id", flat=True)
        queryset = super().get_queryset().filter(
            image__isnull=False, products__id__in=product_ids
        ).distinct('id').order_by("id")
        return queryset


class CategoryViewSet(ReadOnlyModelViewSet):
    """
    Вьюсет отдаёт сплошной список активных категорий. При вызове определённой категории появляется
    дополнительное поле children, которое содержит список дочерних категорий.
    """

    queryset = Category.objects.filter(is_active=True)
    serializer_class_map = {
        "default": CategorySerializer,
        "list": {
            "response": CategorySerializer,
        },
        "get_top_level": {"response": CategoryListSerializer},
    }
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("level", )

    @action(methods=["get"], detail=False)
    def get_top_level(self, request: Request) -> Response:
        """
        Метод возвращает список категорий верхнего уровня
        """
        queryset = self.get_queryset().filter(parent__isnull=True)
        serializer = self.get_response_serializer_class()(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class FavoriteProductsViewSet(ReadOnlyModelViewSet):
    queryset = Product.objects.get_prepared_products()
    filter_backends = (SearchFilter, DjangoFilterBackend)
    filterset_class = ProductOrderingFilter
    serializer_class = ProductListSerializer
    permission_classes = (AllowAny,)


class ProductViewSet(ReadOnlyModelViewSet):
    """
    Вьюсет имеет следующие фильтры: tags, label, category, brand.
    Пример фильтра - /api/products/?label=4. В качестве значения подставляем id объекта, по которому фильтруем.
    Для фильтра по ценам - api/products/?min_price=11&max_price=20
    Для фильтра по размерам - api/products/?variants__characteristics__value=116
    """

    queryset = Product.objects.get_products_on_display()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ProductOrderingFilter
    serializer_class_map = {
        "default": ProductSerializer,
        "list": {
            "response": ProductListSerializer,
        },
        "get_products__with__discount": {
            "response": ProductListSerializer
        },
        "favorites": {
            "response": FavoriteProductSerializer
        },
        "get_products_by_internal_ids": {
            'request': InternalCodeSerializer,
            'response': ProductListSerializer
        }
    }
    filterset_fields = ("tags",)

    @action(methods=('get',), detail=True)
    def favorites(self, request: Request, pk: str = None) -> Response:
        product = self.get_object()
        serializer = self.get_response_serializer(product, many=False)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False)
    def get_filter_params(self, request: Request) -> Response:
        products = self.filter_queryset(self.get_queryset())
        queryset_variants = get_variants__from_products(products=products)
        brands = get_brants__from_products(products=products)
        price_range = get_price_ranges__from_variants(variants=queryset_variants)
        variant_characteristics = get_characteristics__from_variants(variants=queryset_variants)
        data = {
            "characteristics": variant_characteristics,
            "price_range": price_range,
            "brands": brands,
        }
        return Response(data=data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def by_user(self, request: Request) -> Response:
        """
        Метод для получения товаров, находящихся в избранном пользователя. Квери-араметр user_id=1
        """
        user: User = request.user
        if user:
            queryset = user.products.all()
            serializer = self.get_serializer(queryset, many=True)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(data=[], status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def add_to_favorite(self, request: Request) -> Response:
        """
        Метод для добавления товаров в избранное пользователя. Метод принимает post-запрос с полем 'id',
        в которое передаётся id товара.
        """
        products_ids = request.data.get("id").split(",")
        if not products_ids:
            return Response(
                {"message": "No products provided."}, status=status.HTTP_400_BAD_REQUEST
            )
        products = Product.objects.filter(id__in=products_ids)
        if not products:
            return Response(
                {"message": "No valid products provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user: User = request.user
        user.products.add(*products, through_defaults={})
        return Response({"message": f"{len(products)} products added to favorites."})

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def remove_from_favorite(self, request: Request) -> Response:
        """
        Метод для удаления товаров из избранного пользователя. Принимает поле 'id" где указывается список id продуктов,
        которые удаляются из избранного пользователя.
        """
        data = request.data.get("id")
        if data:
            product_ids = data.split(",")
        else:
            product_ids = []

        if not product_ids:
            return Response(
                {"message": "No products provided."}, status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        products = user.products.filter(id__in=product_ids)
        user.products.remove(*products)
        return Response(
            {"message": f"{len(product_ids)} products removed from favorites."}
        )


class VariantViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    queryset = Variant.objects.all()
    serializer_class = VariantSerializer
    serializer_class_map = {
        "default": VariantSerializer,
        "list": {
            "response": VariantSerializer,
        },
        "add_to_basket": {"request": VariantRequestSerializer},
    }

    @action(methods=["patch"], detail=False, permission_classes=[IsAuthenticated])
    def add_to_basket(self, request: Request) -> Response:
        """
        Для добавления товара в корзину:  ключ "variant_id"  значение "id варианта"
        """
        user = request.user
        basket, _ = user.baskets.get_or_create(status=BasketStatus.IS_ACTIVE)
        serializer = self.get_request_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        variant_id = serializer.validated_data.get("variant_id")
        variant = Variant.objects.filter(id=variant_id).first()
        quantity = serializer.validated_data.get("quantity")
        quantity = quantity if quantity else 1
        if quantity > variant.quantity and not variant.to_order:
            quantity = variant.quantity
        item_basket, _ = ItemBasket.objects.get_or_create(
            variant_product_id=variant_id, basket=basket
        )
        item_basket.quantity = quantity
        item_basket.save()
        basket.buy_to_order = checking__products__to_order(basket=basket)
        basket.save()
        return Response(
            data={"message": "Товар добавлен в корзину"}, status=status.HTTP_200_OK
        )


class ItemBasketViewSet(ModelViewSet):
    queryset = ItemBasket.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class_map = {
        "default": ItemBasketSerializer,
        "update": UnloggedItemBasketResponseSerializer,
        "get_unlogged_basket_items": {
            "request": UnloggedItemBasketRequestSerializer,
            "response": UnloggedItemBasketResponseSerializer,
        },
        "adds_from_unlogged_basket": {"request": UnloggedItemBasketRequestSerializer},
    }

    def perform_update(self, serializer: ItemBasketSerializer) -> None:
        if serializer.instance.basket.status != BasketStatus.IS_ACTIVE:
            raise BusinessLogicException()
        variant_quantity = serializer.instance.variant_product.quantity
        to_order = serializer.instance.variant_product.to_order
        quantity = serializer.validated_data.get("quantity")
        if quantity:
            if quantity >= variant_quantity and not to_order:
                serializer.validated_data["quantity"] = variant_quantity
        serializer.save()

    @action(methods=("post",), detail=False, permission_classes=[AllowAny])
    def get_unlogged_basket_items(self, request: Request) -> Response:
        """
        Метод по ключу 'variant_basket' принимает json вида [{'id': <id_варианта>, 'quantity': <количество варианта>},].
        Возвращает данные по выбранным вариантам, их количеству, итоговой стоимости корзины, скидке.
        """
        serializer = self.get_request_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        variants_data = sorted(
            serializer.validated_data.get("variant_basket"), key=lambda x: x["id"]
        )
        variant_ids = [variant["id"] for variant in variants_data]
        variant_quantity = [variant["quantity"] for variant in variants_data]
        variants: QuerySet[Variant] = (
            Variant.objects.get_variant_discount()
            .filter(id__in=variant_ids)
            .order_by("id")
        )
        variants_expenses = [
            {
                "item_cost": variant.price * quantity,
                "item_discount": variant.variant_discount * quantity,
            }
            for variant, quantity in list(zip(variants, variant_quantity))
        ]
        basket_total_cost = sum(map(lambda x: x["item_cost"], variants_expenses))
        basket_discount = sum(map(lambda x: x["item_discount"], variants_expenses))
        basket_with_discount = basket_total_cost - basket_discount
        cost_info = {
            "basket_total_cost": basket_total_cost,
            "basket_discount": basket_discount,
            "basket_with_discount": basket_with_discount,
        }
        items_data = [
            {"variant_product": variant, "quantity": quantity}
            for variant, quantity in zip(variants, variant_quantity)
        ]
        for item in items_data:
            if (
                    item["variant_product"].quantity < item["quantity"]
                    and not item["variant_product"].to_order
            ):
                item["quantity"] = item["variant_product"]
        serializer = self.get_response_serializer(items_data, many=True)
        unlogged_basket_items_data = serializer.data
        data = {"cost_info": cost_info, "basket_elements": unlogged_basket_items_data}
        return Response(data=data, status=status.HTTP_200_OK)

    @action(methods=("post",), detail=False, permission_classes=[IsAuthenticated])
    def adds_from_unlogged_basket(self, request: Request) -> Response:
        serializer = self.get_request_serializer(data=request.data, many=False)
        serializer.is_valid()

        input_data = serializer.validated_data.get("variant_basket")
        variant_ids = list(map(lambda item: item["id"], input_data))

        basket, _ = Basket.objects.get_or_create(
            user=self.request.user, status=BasketStatus.IS_ACTIVE
        )
        objs_matching_with_input_data = basket.item_baskets.filter(
            variant_product__id__in=variant_ids
        ).order_by("variant_product__id")
        matching_input_data: list[dict] = list(
            filter(
                lambda item: item["id"] in objs_matching_with_input_data.values_list(
                    "variant_product__id", flat=True
                ),
                input_data,
            )
        )
        sorted_matched_input_data = list(
            sorted(matching_input_data, key=lambda item: item["id"])
        )
        objs = [
            ItemBasket(id=item.id, quantity=sorted_matched_input_data[num]["quantity"])
            for num, item in enumerate(objs_matching_with_input_data)
        ]
        objs_matching_with_input_data.bulk_update(objs=objs, fields=("quantity",))
        mismatched_input_data = [
            elem for elem in input_data if elem not in matching_input_data
        ]
        try:
            created_objs = [
                ItemBasket(
                    quantity=elem["quantity"],
                    variant_product_id=elem["id"],
                    basket=basket,
                )
                for elem in mismatched_input_data
            ]
            ItemBasket.objects.bulk_create(objs=created_objs, unique_fields=("id",))
        except KeyError:
            raise BusinessLogicException("В теле запроса переданы неверные ключи ")
        return Response(
            data={"message": "Товары добавлены в корзину пользователя"},
            status=status.HTTP_201_CREATED,
        )


class BasketViewSet(ModelViewSet):
    queryset = Basket.objects.all()
    permission_classes = [IsAuthenticated]

    serializer_class_map = {
        "default": BasketSerializer,
        "update": {"request": BasketUpdateSerializer, "response": BasketSerializer},
        "partial_update": {
            "request": BasketUpdateSerializer,
            "response": BasketSerializer,
        },
        "send_payment_url": {
            "request": PaymentUrlsSerializer,
            "response": SuccessfulPaymentSerializer,
        },
        "check_payment_and_inform": {
            "request": TokenInStringSerializer,
        },
    }

    def get_collection(
            self, request_serializer: BaseSerializer
    ) -> Union[list, QuerySet]:
        queryset = super().get_collection(request_serializer=request_serializer)
        return queryset.filter(
            user_id=self.request.user.id, status=BasketStatus.IS_ACTIVE
        )

    def perform_update(self, serializer: BasketUpdateSerializer) -> None:
        basket = serializer.instance
        if basket.status != BasketStatus.IS_ACTIVE:
            raise BusinessLogicException('"Заказ сформирован и изменению не подлежит')
        clear__delivery_method__when__address_data__changes(serializer=serializer)
        clear__payment_method__when__changed__delivery_method__or__address_data(
            serializer=serializer
        )
        check_possible_delivery_methods(serializer=serializer)
        filling_delivery_information_to_basket(serializer=serializer)
        serializer.save()

    @action(methods=["patch"], detail=True)
    def clear_basket(self, request: Request, pk: int = None) -> Response:
        obj: Basket = self.get_object()
        obj.country = None
        obj.city = None
        obj.street_with_type = None
        obj.country_iso_code = None
        obj.flat = None
        obj.unparsed_parts = None
        obj.house = None
        obj.block = None
        obj.geo_lat = None
        obj.geo_lon = None
        obj.city_fias_id = None
        obj.city_kladr_id = None
        obj.block_type_full = None
        obj.house_type_full = None
        obj.region = None
        obj.postal_code = None
        obj.payment_method = None
        obj.address = None
        obj.item_baskets.all().delete()
        obj.save()
        return Response(
            data={"message": "Товары из корзины удалены"}, status=status.HTTP_200_OK
        )

    @action(methods=["post"], detail=True)
    def accept(self, request: Request, pk: int = None) -> Response:
        basket: Basket = self.get_object()
        item_baskets = basket.item_baskets.select_related()
        enough_products_after_revise = checking__products__to_order(basket=basket)
        fixed__item_basket__when_accept(basket=basket, item_baskets=item_baskets)

        basket_cost_data = basket.item_baskets.aggregate(
            without_discount=Sum("item_total_cost"),
            discount=Sum("item_discount"),
            total_cost=ExpressionWrapper(
                F("without_discount") - F("discount"),
                output_field=DecimalField(),
            ),
        )
        basket.total_cost = basket_cost_data["total_cost"]
        basket.discount = basket_cost_data["discount"]
        basket.order_date = datetime.datetime.now(pytz.timezone("Europe/Moscow"))

        check_order_parameters(basket=basket)
        basket.status = BasketStatus.COMPLETED
        basket.save()
        logger.info(f"total_cost - {basket.total_cost}")
        serializer = self.get_response_serializer(instance=basket)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True)
    def send_payment_url(self, request: Request, pk: int) -> Response:
        """Метод получения ссылки на оплату сертификата на указанный email"""
        request_serializer = self.get_request_serializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        response_serializer = self.get_response_serializer(
            instance={
                "url": basket_payment_url(
                    basket=self.get_object(),
                    absolute_uri=request.build_absolute_uri(),
                    payment_success_url=request_serializer.validated_data.get(
                        "payment_success_url"
                    ),
                    payment_fail_url=request_serializer.validated_data.get(
                        "payment_fail_url"
                    ),
                )
            }
        )
        return Response(status=200, data=response_serializer.data)


class OrderViewSet(ModelViewSet):
    queryset = Basket.objects.exclude(status=BasketStatus.IS_ACTIVE)
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self) -> QuerySet[Basket]:
        return (
            super()
            .get_queryset()
            .filter(user=self.request.user)
            .order_by("-order_date")
        )

    @action(methods=("get",), detail=True)
    def get_cdek_order_info(self, request: Request, pk: int = None) -> Response:
        order: Basket = self.get_object()
        cdek_info = get_cdek_info(order=order)
        return Response(cdek_info)
