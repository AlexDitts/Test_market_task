from django import forms
from apps.credentials.models import SMSRuCredentials, EmailCredentials


class SMSRuCredentialsForm(forms.ModelForm):
	class Meta:
		model = SMSRuCredentials
		fields = '__all__'
		widgets = {
			'password': forms.PasswordInput(render_value=True),
		}


class EmailCredentialsForm(forms.ModelForm):
	class Meta:
		model = EmailCredentials
		fields = '__all__'
		widgets = {
			'host_password': forms.PasswordInput(render_value=True),
		}
