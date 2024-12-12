from django.urls import path
from django.contrib.auth.views import LogoutView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView, PasswordResetView
from meal_together.views.users import register_view, login_view, profile_view,edit_profile, activate_view
from meal_together.views.restaurants import create_restaurant, restaurant_list, restaurant_detail
from meal_together.views.general import no_permission_view, redirect_to_sessions_or_login
from meal_together.views.sessions import session_list, create_session, create_order,edit_order, session_detail,session_edit, credit_balance_view, session_summary

urlpatterns = [
    # General
    path('', redirect_to_sessions_or_login, name='home'),
    path('no-permission/', no_permission_view, name='no_permission'),
    # Users
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', profile_view, name='profile'),
    path('edit-profile/', edit_profile, name='edit_profile'),
    path('activate/<str:uidb64>/<str:token>/', activate_view, name='activate'),
    # Restaurants
    path('restaurants/', restaurant_list, name='restaurant_list'),
    path('restaurants/create/', create_restaurant, name='create_restaurant'),
    path('restaurants/<int:restaurant_id>/', restaurant_detail, name='restaurant_detail'),
    # Sessions
    path('sessions/', session_list, name='session_list'),
    path('sessions/create/', create_session, name='create_session'),
    path('sessions/<int:session_id>/', session_detail, name='session_detail'),
    path('sessions/<int:session_id>/create_order/<int:user_id>/', create_order, name='create_order'),
    path('sessions/<int:session_id>/edit_order/<int:user_id>/', edit_order, name='edit_order'),
    path('sessions/<int:session_id>/edit/', session_edit, name='session_edit'),
    path('sessions/<int:session_id>/summary/', session_summary, name='session_summary'),
    path('credit_balance/', credit_balance_view, name='credit_balance'),
    # Password reset
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
