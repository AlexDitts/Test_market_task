from decimal import Decimal

import django_filters.rest_framework as filters
from celery.result import AsyncResult
from django.db.models import Max, Min, Q, QuerySet

from apps.market.models import Category, Product
from apps.market.tasks import (get_products__by__article,
                               get_products__by__brand__name,
                               get_products__by__characteristics_value,
                               get_products__by__code,
                               get_products__by__description,
                               get_products__by__name,
                               get_products__by__variants__code)


class ProductOrderingFilter(filters.FilterSet):
    class Meta:
        model = Product
        fields = (
            'ordering',
            'brand',
            'characteristics_value',
            'price_range',
            'category',
            'label',
            'tags',
            'id',
            'user'
        )

    user = filters.CharFilter(
        method='filter_by_user_id',
        label='user_id',
        help_text='Filter by user id'
    )

    id = filters.CharFilter(
        method='filter_by_ids',
        label='id',
        help_text='Filter by list id'
    )

    ordering = filters.CharFilter(
        method='ordering_price',
        label='Ordering',
        help_text='Ordering by variant.price'
    )
    label = filters.CharFilter(
        method='label_filter',
        label='Label',
        help_text='Filter products by label id'
    )
    type_label = filters.CharFilter(
        method='type_label_filter',
        label='type_Label',
        help_text='Filter products by type label id'
    )
    with_discount = filters.CharFilter(
        method='filter_products_with_discount',
        label='with_discount',
        help_text='Filter products by sale_price > 0'
    )
    brand = filters.CharFilter(
        method='brand_filter',
        label='Brand',
        help_text='Filter products by brands. Sample of requests:'
                  'api/products/?brand=value1,value2,value3'
    )
    category = filters.CharFilter(
        method='category_filter',
        label='category',
        help_text='Filter products by category. Sample of requests:'
                  'api/products/?category=1,2,3'
    )
    characteristics_value = filters.CharFilter(
        method='characteristics_filter',
        label='Characteristics Value',
        help_text='Filter products by characteristics value. Sample of requests:'
                  'api/products/?characteristics_value=value1,value2,value3'
    )
    price_range = filters.CharFilter(
        method='price_range_filter',
        label='Price Range',
        help_text='Filter products by price range. Sample of requests:'
                  'api/products/?price_range=10,100'
    )
    tags = filters.CharFilter(
        method='tags_filter',
        label='Tags_filter',
        help_text='Filter products by tags'
    )
    # search = filters.CharFilter(
    #     method='search_filter',
    #     label='search_filter',
    #     help_text='Filter products by search.',
    # )

    # def search_filter(self, queryset: QuerySet[Product], name: str, value: str) -> QuerySet[Product]:
    #
    #     characteristics_records: AsyncResult = get_products__by__characteristics_value.apply_async((value, ))
    #     article_records: AsyncResult = get_products__by__article.apply_async((value, ))
    #     name_records: AsyncResult = get_products__by__name.apply_async((value, ))
    #     code_records: AsyncResult = get_products__by__code.apply_async((value, ))
    #     description_records: AsyncResult = get_products__by__description.apply_async((value, ))
    #     brands_records: AsyncResult = get_products__by__brand__name.apply_async((value, ))
    #     variants_records: AsyncResult = get_products__by__variants__code.apply_async((value, ))
    #     article_results = article_records.get().get('data')
    #     name_results = name_records.get().get('data')
    #     code_results = code_records.get().get('data')
    #     description_results = description_records.get().get('data')
    #     brands_results = brands_records.get().get('data')
    #     variants_results = variants_records.get().get('data')
    #     characteristics_results = characteristics_records.get().get('data')
    #     article_results.extend(name_results)
    #     article_results.extend(code_results)
    #     article_results.extend(description_results)
    #     article_results.extend(brands_results)
    #     article_results.extend(variants_results)
    #     article_results.extend(characteristics_results)
    #     product_ids = list(set(article_results))
    #     combined_results = queryset.filter(id__in=product_ids)
    #     return combined_results

    def filter_by_ids(self, queryset: QuerySet[Product], name: str, value: str) -> QuerySet[Product]:
        return queryset.filter(id__in=value.split(','))

    def ordering_price(self, queryset: QuerySet[Product], name: str, value: str) -> QuerySet[Product]:
        queryset = queryset.annotate(min_price=Min('variants__price'), max_price=Max('variants__price'))
        if value.startswith('-'):
            return queryset.order_by('-min_price')
        return queryset.order_by('max_price')

    def tags_filter(self, queryset: QuerySet[Product], name: str, value: str) -> QuerySet[Product]:
        return queryset.filter(tags__id__in=value.split(','))

    def label_filter(self, queryset: QuerySet[Product], name: str, value: str) -> QuerySet[Product]:
        return queryset.filter(label_id__in=value.split(','))

    def brand_filter(
            self, queryset: QuerySet[Product], name: str, value: str
    ) -> QuerySet[Product]:
        """Возвращает данные отфильтрованные по бренду товара."""
        return queryset.filter(brand_id__in=value.split(','))

    def price_range_filter(
            self, queryset: QuerySet[Product], name: str, value: str
    ) -> QuerySet[Product]:
        values_to_list_decimal = list(map(lambda x: Decimal(x), value.split(',')))
        return queryset.filter(price_for_filter__range=values_to_list_decimal)

    def characteristics_filter(
            self, queryset: QuerySet[Product], name: str, value: str
    ) -> QuerySet[Product]:
        return queryset.filter(
            Q(variants__characteristics__value__in=value.split(','))
            & Q(Q(variants__stock__gt=0) | Q(variants__to_order=True))
            & Q(Q(variants__is_active=True))
        )

    def category_filter(
            self, queryset: QuerySet[Product], name: str, value: str
    ) -> QuerySet[Product]:
        category = Category.objects.filter(id=value.split(',')[0], is_active=True).first()
        if category:
            tree_categories_id = category.get_descendants(include_self=True).values_list('id', flat=True)
            return queryset.filter(category__id__in=tree_categories_id)
        return queryset.none()

    def filter_by_user_id(
            self, queryset: QuerySet[Product], name: str, value: str
    ) -> QuerySet[Product]:
        return queryset.filter(user__id=value.split(',')[0])

    def type_label_filter(
            self, queryset: QuerySet[Product], name: str, value: str
    ) -> QuerySet[Product]:
        if value == 'promotion':
            return queryset.filter(variants__price__gt=0)
        return queryset.filter(label__type_label=value.split(',')[0], variants__sale_price=0)

    def filter_products_with_discount(
            self, queryset: QuerySet[Product], name: str, value: str
    ) -> QuerySet[Product]:
        if value.split(',')[0] == "1":
            return queryset.filter(variants__sale_price__gt=0)
        return queryset
