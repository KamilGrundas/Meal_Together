from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from meal_together.models.users import CustomUser
from meal_together.models.restaurants import Tag, Restaurant, MenuItem
from meal_together.models.sessions import MealSession, Order

admin.site.register(CustomUser, UserAdmin)
admin.site.register(Tag)
admin.site.register(Restaurant)
admin.site.register(MenuItem)
admin.site.register(MealSession)
admin.site.register(Order)
