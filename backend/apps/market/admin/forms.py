from ckeditor.widgets import CKEditorWidget
from django import forms
from django.forms import TextInput

from apps.content.models import Contact
from apps.market.models import Brand, Category, Product


class SetCategoryForm(forms.Form):
    _selected_action = forms.CharField(
        widget=forms.MultipleHiddenInput(),
        label="hidden",
    )
    category = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        label="Категории",
    )


class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"
        widgets = {
            "text_under_title": CKEditorWidget(),
            "text_under_product": CKEditorWidget()
        }


class BrandAdminForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = "__all__"
        widgets = {
            "text_under_title": CKEditorWidget(),
            "text_under_product": CKEditorWidget()
        }
