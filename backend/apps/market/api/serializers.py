from decimal import Decimal

from django.db.models import Avg, Case, Count, F, Max, Min, Q, Sum
from rest_framework import serializers
from restdoctor.rest_framework.serializers import ModelSerializer

from apps.market.enum import TypeLabel
from apps.market.logic.interactors.basket_interactors import  check_another_variants

from apps.market.models import (Basket, Brand, Category, Characteristic,
                                ItemBasket, Label, OrderState, Product,
                                ProductCharacteristics, ProductImage, Tag,
                                Variant, VariantCharacteristics)
from apps.shipping_and_payment.models import PaymentVariant
from config.settings import DOMAIN


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = "__all__"

    image = serializers.SerializerMethodField()
    miniature = serializers.SerializerMethodField()

    def get_image(self, obj: ProductImage) -> dict:
        if obj.image:
            return obj.image.url

    def get_miniature(self, obj: ProductImage) -> dict:
        if obj.miniature:
            return obj.miniature.url


class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class CategorySerializer(CategoryListSerializer):
    class Meta:
        model = Category
        fields = "__all__"

    children = serializers.SerializerMethodField()
    category_image = serializers.SerializerMethodField()
    tree_cat = serializers.SerializerMethodField()

    def get_tree_cat(self, obj: Category) -> dict:
        return obj.get_family().values()

    def get_category_image(self, obj: Category) -> dict:
        if obj.category_image:
            return obj.category_image.url

    def get_children(self, obj: Category) -> dict:
        return obj.get_children().values()


class CharacteristicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Characteristic
        fields = "__all__"


class VariantCharacteristicsSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantCharacteristics
        fields = "__all__"

    type = CharacteristicSerializer(many=False)


class VariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variant
        fields = "__all__"

    characteristics = VariantCharacteristicsSerializer(many=True)
    preview = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()

    def get_label(self, obj: Variant) -> dict:
        return LabelSerializer(obj.product.label).data

    def get_preview(self, obj: Variant) -> str:
        return obj.product.images.filter(priority=0).values("miniature").first()


class VariantRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variant
        fields = ("variant_id", "quantity")

    variant_id = serializers.CharField()
    quantity = serializers.IntegerField(allow_null=True)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        exclude = ("type_label",)


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = "__all__"

    image = serializers.SerializerMethodField()

    def get_image(self, obj: Brand) -> dict | None:
        image = obj.image
        if image:
            return obj.image.url


class ProductCharacteristicSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCharacteristics
        fields = "__all__"

    type = CharacteristicSerializer(many=False)


class InternalCodeSerializer(serializers.Serializer):
    internal_id_list = serializers.ListField(child=serializers.IntegerField())


class ProductListSerializer(ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "price_variants",
            "image_preview",
            "label",
            "brand",
            "price_label",
            "h1",
            "custom_item_title",
            "updated_at",
            "variants"
        )

    price_variants = serializers.SerializerMethodField()
    image_preview = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()
    price_label = serializers.SerializerMethodField()
    custom_item_title = serializers.SerializerMethodField()
    h1 = serializers.SerializerMethodField()

    def get_custom_item_title(self, obj: Product) -> str | None:
        return obj.characteristics.filter(type__name__endswith='item_title').values_list('value', flat=True).first()

    def get_h1(self, obj: Product) -> dict:
        return obj.characteristics.filter(type__name='h1').values_list('value', flat=True).first()

    def get_label(self, obj: Product) -> dict:
        if obj.variants.filter(
                Q(sale_price__isnull=True) | Q(sale_price__gt=0)
        ).exists():
            return Label.objects.filter(type_label=TypeLabel.PROMOTION).values().first()
        return LabelSerializer(obj.label).data

    def get_price_variants(self, obj: Product) -> dict:
        return obj.variants.exclude(price=0).values("price", "sale_price")

    def get_image_preview(self, obj: Product) -> dict:
        return obj.images.filter(priority=0).filter().values("miniature").first()

    def get_price_label(self, obj: Product) -> dict:
        variants = obj.variants.filter(
            Q(is_active=True) & Q(price__gt=0) & Q(Q(quantity__gt=0) | Q(to_order=True))
        )
        if variants.filter(sale_price__gt=0).exists():
            label_price = (
                variants.filter(sale_price__gt=0)
                .order_by("sale_price")
                .values("sale_price", "price")
                .first()
            )
            return {
                "price_discount": label_price.get("sale_price"),
                "price": label_price.get("price"),
                "min_price": None,
                "max_price": None,
            }

        else:
            variants_with_avg_price = variants.annotate(avg_price=Avg("price"))
            if variants_with_avg_price.exclude(price=F("avg_price")).exists():
                price = variants.annotate(
                    min_price=Min("price"), max_price=Max("price")
                ).values("min_price", "max_price")
                return {
                    "price_discount": None,
                    "price": None,
                    "min_price": price.get("min_price"),
                    "max_price": price.get("max_price"),
                }
            if variants_with_avg_price.exists():
                return {
                    "price_discount": None,
                    "price": None,
                    "min_price": variants_with_avg_price.order_by("price")
                    .first()
                    .price,
                    "max_price": variants_with_avg_price.order_by("-price")
                    .first()
                    .price,
                }


class RecommendetProductSerializer(ProductListSerializer):
    pass


class ProductSerializer(ProductListSerializer):
    class Meta:
        model = Product
        fields = (
            "id",
            "archived",
            "name",
            "code",
            "description",
            "external_code",
            "price_label",
            "article",
            "weight",
            "volume",
            "updated_at",
            "is_active",
            "brand",
            "category",
            "label",
            "image_preview",
            "label",
            "brand",
            "crossale",
            "tags",
            "variants",
            "images",
            "characteristics",
            "h1",
            "custom_item_title"
        )

    label = LabelSerializer(many=False)
    images = ProductImageSerializer(many=True)
    variants = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)
    brand = BrandSerializer(many=False)
    category = CategorySerializer(many=True)
    characteristics = ProductCharacteristicSerializer(many=True)
    crossale = serializers.SerializerMethodField()

    def get_crossale(self, obj: Product) -> list[dict]:
        crossale = obj.crossale.annotate(
            price_variants=Sum("variants__price"),
            quantity_variants=Sum("variants__quantity"),
            to_order_variants=Count("variants", filter=Q(variants__to_order=True)),
        ).exclude(
            Q(category__isnull=True)
            | Q(price_variants=0)
            | Q(is_active=False)
            | Q(Q(quantity_variants=0) & Q(to_order_variants=False))
        )
        return RecommendetProductSerializer(crossale, many=True).data

    def get_variants(self, obj: Product) -> list:
        return VariantSerializer(
            obj.variants.filter(
                Q(
                    Q(quantity__gt=0) | Q(to_order=True)
                )
                & Q(is_active=True)
                & Q(price__gt=0)
            ), many=True
        ).data


class FavoriteProductSerializer(ProductSerializer):
    variants = serializers.SerializerMethodField(method_name='get_variants')

    def get_variants(self, obj: Product) -> list[dict]:
        variants = obj.variants.all().filter(price__gt=0, is_active=True)
        return VariantSerializer(variants, many=True).data


class ItemBasketSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemBasket
        fields = "__all__"
        read_only_fields = (
            "id",
            "code",
            "name",
            "article",
            "price",
            "sale_price",
            "item_total_cost",
            "item_total_cost_with_discount",
            "discount",
            "settlement_discount",
            "settlement_total_cost",
            "settlement_total_cost_with_discount",
            "variant_product",
            "has_another_variant",
            "basket",
        )

    variant_product = VariantSerializer(many=False)
    has_another_variant = serializers.SerializerMethodField()

    def get_has_another_variant(self, obj: ItemBasket) -> bool:
        if (not obj.variant_product.quantity) and (not obj.variant_product.to_order):
            return check_another_variants(item=obj)
        return True


class UnloggedItemBasketRequestSerializer(serializers.Serializer):
    class Meta:
        fields = ("variant_basket",)

    variant_basket = serializers.JSONField()


class UnloggedItemBasketResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemBasket
        fields = ("variant_product", "quantity")
        read_only_fields = ("variant_product", "quantity")

    quantity = serializers.IntegerField(allow_null=True)
    variant_product = VariantSerializer(many=False, allow_null=True)


class PaymentVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentVariant
        fields = "__all__"


class OrderStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderState
        fields = "__all__"


class BasketUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Basket
        fields = (
            "customer_name",
            "customer_surname",
            "customer_email",
            "customer_phone",
            "address",
            "city",
            "country",
            "pvz_code",
            "payment_method",
            "postal_code",
            "country",
            "city",
            "region",
            "street_with_type",
            "house_type_full",
            "house",
            "block_type_full",
            "block",
            "flat",
            "unparsed_parts",
            "geo_lat",
            "geo_lon",
            "country_iso_code",
            "city_fias_id",
            "city_kladr_id",
        )


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Basket
        fields = (
            "id",
            "status",
            "total_cost",
            "discount",
            "order_number",
            "order_state",
            "customer_phone",
            "customer_name",
            "customer_surname",
            "customer_email",
            "payment_status",
            "order_date",
            "order_name",
            "payment_id",
            "user",
            "address",
            "city",
            "country",
            "pvz_code",
            "payment_method",
            "expenses",
            "count_variants",
            "item_baskets",
            "country",
            "city",
            "postal_code",
            "region",
            "street_with_type",
            "house_type_full",
            "house",
            "block_type_full",
            "block",
            "flat",
            "unparsed_parts",
            "geo_lat",
            "geo_lon",
            "country_iso_code",
            "city_fias_id",
            "city_kladr_id",
            "payment_url",
        )

    order_date = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")
    order_state = OrderStateSerializer(read_only=True)
    payment_method = serializers.SerializerMethodField()
    expenses = serializers.SerializerMethodField()
    count_variants = serializers.SerializerMethodField()
    item_baskets = ItemBasketSerializer(many=True)

    def get_count_variants(self, obj: Basket) -> dict:
        return obj.item_baskets.count()

    def get_expenses(self, obj: Basket) -> dict:
        data_cost = obj.item_baskets.get_cost_info()
        return data_cost.aggregate(
            basket_without_discount=Sum("without_discount"),
            basket_discount=Sum("item_total_discount"),
            basket_with_discount=F("basket_without_discount") - F("basket_discount"),
            basket_final_cost=F("basket_with_discount")
        )


class BasketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Basket
        fields = (
            "id",
            "status",
            "total_cost",
            "discount",
            "order_number",
            "customer_phone",
            "customer_name",
            "customer_surname",
            "customer_email",
            "payment_status",
            "order_date",
            "order_name",
            "payment_id",
            "user",
            "address",
            "city",
            "country",
            "payment_method",
            "available_payment_method",
            "expenses",
            "count_variants",
            "settlement_data_cost",
            "item_baskets",
            "country",
            "city",
            "postal_code",
            "region",
            "street_with_type",
            "house_type_full",
            "house",
            "block_type_full",
            "block",
            "flat",
            "unparsed_parts",
            "geo_lat",
            "geo_lon",
            "country_iso_code",
            "city_fias_id",
            "city_kladr_id",
            "payment_url",
        )

    order_date = serializers.SerializerMethodField()

    available_payment_method = serializers.SerializerMethodField(read_only=True)
    expenses = serializers.SerializerMethodField()
    count_variants = serializers.SerializerMethodField()
    settlement_data_cost = serializers
    item_baskets = ItemBasketSerializer(many=True)

    def get_payment_method(self, obj: Basket) -> dict:
        if obj.payment_method:
            payment_method = PaymentVariant.objects.filter(
                name=obj.payment_method
            ).first()
            return {
                "key": payment_method.name,
                "name": payment_method.get_name_display(),
            }

    def get_order_date(self, obj: Basket) -> str:
        if obj.order_date:
            return obj.order_date.strftime("%d.%m.%Y %H:%M:%S")

    def get_available_payment_method(self, obj: Basket) -> list:
        return PaymentVariant.objects.values()

    def get_count_variants(self, obj: Basket) -> dict:
        return obj.item_baskets.count()

    def get_expenses(self, obj: Basket) -> dict:
        data_cost = obj.item_baskets.get_cost_info()
        return data_cost.aggregate(
            basket_without_discount=Sum("without_discount"),
            basket_discount=Sum("item_total_discount"),
            basket_with_discount=F("basket_without_discount") - F("basket_discount"),
            basket_final_cost=F("basket_with_discount")
        )

    def get_settlement_data_cost(self, obj: Basket) -> dict:
        data_cost = obj.item_baskets.get_settlement_cost_info()
        data = data_cost.aggregate(
            basket_full_cost=Sum("settlement_total_price"),
            basket_discount=Sum("settlement_discount"),
            basket_with_discount=F("basket_full_cost") - F("basket_discount"),
            basket_final_cost=F("basket_with_discount")
        )
        return data


class SuccessfulPaymentSerializer(serializers.Serializer):
    url = serializers.CharField(help_text="URL на оплату")


class PaymentUrlsSerializer(serializers.Serializer):
    payment_success_url = serializers.URLField(
        help_text="URL при успешной оплате", required=False
    )
    payment_fail_url = serializers.URLField(
        help_text="URL при неуспешной оплате ", required=False
    )


class TokenInStringSerializer(serializers.Serializer):
    token = serializers.CharField(help_text="токен")


class YandexOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            'name',
            'vendor',
            'vendorCode',
            'url',
            'price',
            'oldprice',
            'enable_auto_discounts',
            'currencyId',
            'categoryId',
            'picture',
            'description',
            'sales_notes',
            'manufacturer_warranty',
            'barcode',
            'attrib',
            'param',
        )

    name = serializers.SerializerMethodField()
    vendor = serializers.SerializerMethodField()
    vendorCode = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    oldprice = serializers.SerializerMethodField()
    enable_auto_discounts = serializers.SerializerMethodField()
    currencyId = serializers.SerializerMethodField()
    categoryId = serializers.SerializerMethodField()
    picture = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    sales_notes = serializers.SerializerMethodField()
    manufacturer_warranty = serializers.SerializerMethodField()
    barcode = serializers.SerializerMethodField()
    param = serializers.SerializerMethodField()
    attrib = serializers.SerializerMethodField()

    def get_attrib(self, obj: Product) -> dict:
        return {'id': str(obj.internal.id), 'available': str(True).lower()}

    def get_name(self, obj: Product) -> str:
        characteristics = obj.characteristics.filter(type__name='h1')
        if characteristics.exists():
            name = characteristics.first().value
            return name
        return obj.name

    def get_vendor(self, obj: Product) -> str:
        if obj.brand:
            return obj.brand.name

    def get_vendorCode(self, obj: Product) -> str:
        return obj.article

    def get_url(self, obj: Product) -> str:
        return f'{DOMAIN}/product/{obj.id}'

    def get_price(self, obj: Product) -> str:
        if obj.variants.all():
            return str(obj.variants.exclude(price=0).annotate(
                min_price=Min("price", filter=Q(price__isnull=False)),
            ).values('min_price').first().get('min_price'))

    def get_oldprice(self, obj: Product) -> Decimal:
        if obj.variants.all():
            return obj.variants.annotate(
                min_old_price=Min("sale_price", filter=Q(sale_price__isnull=False))
            ).values('min_old_price').first()['min_old_price']

    def get_enable_auto_discounts(self, obj: Product) -> str:
        return str(True).lower()

    def get_currencyId(self, obj: Product) -> str:
        return 'RUR'

    def get_categoryId(self, obj: Product) -> str:
        if obj.category.first():
            return obj.category.values_list('id', flat=True).first()

    def get_picture(self, obj: Product) -> str:
        if obj.images.first():
            return obj.images.first().image.url

    def get_param(self, obj: Product) -> list:
        sizes = obj.variants.annotate(
            name_param=F('characteristics__type__name'),
            value=F('characteristics__value')
        ).values_list('name_param', 'value')
        return list(sizes)

    def get_barcode(self, obj: Product) -> str | None:
        return None

    def get_description(self, obj: Product) -> str:
        return obj.description

    def get_sales_notes(self, obj: Product) -> str:
        return ''

    def get_manufacturer_warranty(self, obj: Product) -> str:
        return str(True).lower()

    def get_weight(self, obj: Product) -> Decimal:
        return obj.weight
