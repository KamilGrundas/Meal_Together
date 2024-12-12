from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from meal_together.models.restaurants import Restaurant, MenuItem
from meal_together.forms.restaurants import RestaurantForm, MenuItemForm
from itertools import groupby

def is_manager_or_admin(user):
    return user.is_superuser or user.groups.filter(name='Manager').exists()

@login_required
def restaurant_list(request):
    restaurants = Restaurant.objects.all()
    user_in_group = request.user.groups.filter(name__in=['Manager', 'Admin']).exists()
    return render(request, 'restaurants/restaurant_list.html', {
        'restaurants': restaurants,
        'user_in_group': user_in_group
    })


@login_required
@user_passes_test(is_manager_or_admin, login_url='/no-permission/')
def create_restaurant(request):
    if request.method == 'POST':
        form = RestaurantForm(request.POST)
        if form.is_valid():
            restaurant = form.save(commit=False)
            restaurant.owner = request.user
            restaurant.save()
            form.save_m2m()
            return redirect('restaurant_detail',restaurant_id=restaurant.id)
    else:
        form = RestaurantForm()
    return render(request, 'restaurants/create_restaurant.html', {'form': form})


@login_required
def restaurant_detail(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    menu_items = MenuItem.objects.filter(restaurant=restaurant).order_by('item_type')

    grouped_menu = {}
    for item_type, items in groupby(menu_items, lambda x: x.item_type):
        grouped_menu[item_type] = list(items)

    user_in_group = request.user.is_authenticated and request.user.groups.filter(name__in=['Manager', 'Admin']).exists()

    if request.method == 'POST' and user_in_group:
        form = MenuItemForm(request.POST)
        if form.is_valid():
            new_item = form.save(commit=False)
            new_item.restaurant = restaurant
            new_item.save()
            return redirect('restaurant_detail', restaurant_id=restaurant.id)
    else:
        form = MenuItemForm()

    return render(request, 'restaurants/restaurant_detail.html', {
        'restaurant': restaurant,
        'grouped_menu': grouped_menu,
        'user_in_group': user_in_group,
        'form': form
    })
