from django.db.models import QuerySet
from rest_framework import serializers

from apps.content.logic.ineractors.interactor import apportioned_children
from apps.content.models import (FAQ, About, AboutImage, Banner,
                                 Contact, DeliveryMethod, Documents, Header,
                                 ReturnConditions)
from apps.market.models import Category


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documents
        fields = '__all__'

    user_agreement = serializers.SerializerMethodField()
    privacy_policy = serializers.SerializerMethodField()
    cookie_policy = serializers.SerializerMethodField()

    def get_user_agreement(self, obj: Documents) -> str:
        if obj.user_agreement:
            return obj.user_agreement.url

    def get_privacy_policy(self, obj: Documents) -> str:
        if obj.privacy_policy:
            return obj.privacy_policy.url

    def get_cookie_policy(self, obj: Documents) -> str:
        if obj.cookie_policy:
            return obj.cookie_policy.url


class AboutImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutImage
        fields = '__all__'

    image = serializers.SerializerMethodField()

    def get_image(self, obj: AboutImage) -> dict[str, str]:
        return obj.image.url


class AboutSerializer(serializers.ModelSerializer):
    class Meta:
        model = About
        fields = ("text1", 'image1', "text2", "image2", "text3", "image3")

        image1 = serializers.SerializerMethodField()
        image2 = serializers.SerializerMethodField()
        image3 = serializers.SerializerMethodField()

        def get_image1(self, obj: About) -> dict[str, str]:
            return obj.image1.url

        def get_image2(self, obj: About) -> dict[str, str]:
            return obj.image2.url

        def get_image3(self, obj: About) -> dict[str, str]:
            return obj.image3.url


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = '__all__'

    banner_image = serializers.SerializerMethodField()
    adaptive_image = serializers.SerializerMethodField()

    def get_banner_image(self, obj: Banner) -> dict[str, str]:
        return obj.banner_image.url

    def get_adaptive_image(self, obj: Banner) -> dict[str, str]:
        return obj.adaptive_image.url


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'


class DeliveryMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryMethod
        fields = '__all__'


class ReturnConditionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnConditions
        fields = '__all__'

