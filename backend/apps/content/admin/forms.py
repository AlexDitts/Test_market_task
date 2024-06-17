from ckeditor_uploader.widgets import CKEditorUploadingWidget

from django import forms

from apps.content.models import About, FAQ, ReturnConditions, Contact


class AboutAdminForm(forms.ModelForm):
    class Meta:
        model = About
        fields = '__all__'
        widgets = {
            'text1': CKEditorUploadingWidget(),
            'text2': CKEditorUploadingWidget(),
            'text3': CKEditorUploadingWidget()
        }


class ContactAdminForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = '__all__'
        widgets = {
            "phone_number": forms.TextInput(attrs={'class': 'tel', 'placeholder': 'Номер телефона'}),
            "whatsapp1": forms.TextInput(attrs={'class': 'tel', 'placeholder': 'Номер телефона'}),
            "whatsapp2": forms.TextInput(attrs={'class': 'tel', 'placeholder': 'Номер телефона'}),
        }


class FAQAdminForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = '__all__'
        widgets = {
            'question': CKEditorUploadingWidget(),
            'answer': CKEditorUploadingWidget(),
        }


class ReturnConditionsFormAdmin(forms.ModelForm):
    class Meta:
        model = ReturnConditions
        fields = '__all__'
        widgets = {
            'text': CKEditorUploadingWidget(),
        }

