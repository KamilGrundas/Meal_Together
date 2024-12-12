from django import forms
from django.core.exceptions import ValidationError
from meal_together.models.restaurants import Restaurant, MenuItem, Tag
import re

class RestaurantForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Restaurant
        fields = ['name', 'address', 'phone_number', 'tags']
        widgets = {
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter restaurant address'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number', '').strip()
        if not re.match(r'^\+?\d{7,15}$', phone_number):
            raise ValidationError(
                "Invalid phone number. It must contain only digits and can optionally start with '+'."
            )
        return phone_number


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['item_type', 'name', 'price', 'currency']
