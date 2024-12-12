from django.shortcuts import render, redirect
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import login, get_user_model
from meal_together.helpers import account_activation_token
from meal_together.emails import send_activation_link
from django.utils.encoding import force_str
from meal_together.forms.users import EmailLoginForm, UserEditForm, UserRegistrationForm
from django.contrib.auth.models import Group

User = get_user_model()


def register_view(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            send_activation_link(current_site, user)

            return render(request, "users/account_activation_sent.html")
    else:
        form = UserRegistrationForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = EmailLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")
    else:
        form = EmailLoginForm()
    return render(request, "users/login.html", {"form": form})


@login_required
def profile_view(request):
    return render(request, "users/profile.html", {"user": request.user})


@login_required
def edit_profile(request):
    user = request.user
    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect("profile")
    else:
        form = UserEditForm(instance=user)
    return render(request, "users/edit_profile.html", {"form": form})


def activate_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        customer_group, created = Group.objects.get_or_create(name="Customer")
        user.is_active = True
        user.groups.add(customer_group)
        user.save()
        return render(request, "users/account_activation_success.html")
    else:
        return render(request, "users/account_activation_invalid.html")
