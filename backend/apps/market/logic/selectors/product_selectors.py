from django.db.models import QuerySet, Q, Max, Min, Case, When, F
from django.db.models.functions import Least

from apps.market.models import Variant, Product, Brand


def get_variants__from_products(products: QuerySet[Product]) -> QuerySet:
    queryset_variants = Variant.objects.filter(
            Q(product_id__in=products)
            & Q(price__gt=0)
            & Q(Q(quantity__gt=0) | Q(to_order=True))
        )
    return queryset_variants


def get_brants__from_products(*, products: QuerySet[Product]) -> QuerySet:
    brands = Brand.objects.filter(
        products__id__in=products.values_list('id', flat=True)
    ).values('id', 'name').order_by('name', 'id').distinct('name', 'id')
    return brands


def get_price_ranges__from_variants(*, variants: QuerySet[Variant]) -> QuerySet:
    price_range = variants.only("price", "sale_price").aggregate(
        max_price=Max("price"),
        min_price=Min(
            Case(
                When(sale_price__gt=0, then=Least(F("sale_price"), F("price"))),
                default="price",
            )
        ),
    )
    return price_range


def get_characteristics__from_variants(*, variants: QuerySet[Variant]) -> QuerySet:
    variant_characteristics = variants.filter(product__exclude_from_filter=False).annotate(
            params=F("characteristics__type__name"),
            sizes=F("characteristics__value"),
        ).distinct("sizes").values("params", "sizes")
    return variant_characteristics


def get_products__by_internal_ids(*, queryset: QuerySet[Product], list_ids: list[int]) -> QuerySet:
    qs = queryset.filter(internal__id__in=list_ids)
    return qs


def get_products__empty() -> QuerySet[Product]:
    return Product.objects.none()

