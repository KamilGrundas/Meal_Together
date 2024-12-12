from django.db import models
from django.contrib.auth import get_user_model
from meal_together.models.restaurants import Restaurant, MenuItem
from django.utils.timezone import now

User = get_user_model()

class MealSession(models.Model):
    name = models.CharField(max_length=255)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='sessions')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_sessions')
    participants = models.ManyToManyField(User, related_name='invited_sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_time = models.DateTimeField()
    order_deadline = models.DateTimeField()
    email_sent = models.BooleanField(default=False)

    def is_active(self):
        return now() <= self.order_deadline

    def total_spent_by_user(self, user):
        return sum(order.total_price for order in self.orders.filter(user=user))
    

    def __str__(self):
        return self.name


class Order(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('Blik', 'Blik'),
        ('Cash', 'Cash'),
        ('Credit', 'Credit'),
    ]
    session = models.ForeignKey('MealSession', on_delete=models.CASCADE, related_name='orders')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        default='Cash',
    )
    items = models.ManyToManyField('MenuItem', through='OrderItem', related_name='orders')

    def __str__(self):
        return f"Order #{self.id}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    menu_item = models.ForeignKey('MenuItem', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    note = models.TextField(blank=True, null=True)

    @property
    def item_total_price(self):
        return self.menu_item.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name} for Order #{self.order.id}"

