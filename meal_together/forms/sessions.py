from django import forms
from django.utils.timezone import localtime
from meal_together.models.sessions import MealSession, Order, OrderItem
from django.forms import inlineformset_factory
from meal_together.models.restaurants import MenuItem
from django.contrib.auth import get_user_model

User = get_user_model()

from django.utils.timezone import localtime, make_aware, is_naive
from django.contrib.auth.models import Group

class MealSessionForm(forms.ModelForm):
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Invite Participants'
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Invite Groups'
    )

    order_deadline = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label='Order Deadline',
    )

    delivery_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label='Delivery Time',
    )

    class Meta:
        model = MealSession
        fields = ['name', 'restaurant', 'order_deadline', 'delivery_time', 'participants', 'groups']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.initial['order_deadline'] = localtime(self.instance.order_deadline).strftime('%Y-%m-%dT%H:%M')
            self.initial['delivery_time'] = localtime(self.instance.delivery_time).strftime('%Y-%m-%dT%H:%M')
        else:
            # Set default values for new instances
            self.initial['order_deadline'] = localtime().strftime('%Y-%m-%dT%H:%M')
            self.initial['delivery_time'] = localtime().strftime('%Y-%m-%dT%H:%M')

        if user:
            excluded_group_names = ['Admin', 'Customer', 'Manager']
            self.fields['groups'].queryset = Group.objects.exclude(name__in=excluded_group_names)

            self.fields['participants'].queryset = User.objects.exclude(id=user.id)
            self.fields['participants'].label_from_instance = lambda obj: f'{obj.first_name} {obj.last_name} (@{obj.username})'

    def clean_order_deadline(self):
        return self.cleaned_data['order_deadline']

    def clean_delivery_time(self):
        return self.cleaned_data['delivery_time']


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['payment_method']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
        }

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity', 'note']
        widgets = {
            'menu_item': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

OrderItemFormSet = inlineformset_factory(
    Order,
    OrderItem,
    form=OrderItemForm,
    extra=3,
    can_delete=True
)