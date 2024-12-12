from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required
from meal_together.models.sessions import MealSession, Order
from meal_together.models.restaurants import MenuItem
from meal_together.forms.sessions import (
    MealSessionForm,
    OrderItemFormSet,
    OrderForm,
)
from meal_together.helpers import (
    get_order_changes,
    get_session_changes,
    process_participants,
    aggregate_order_items,
    get_orders_as_creditor,
    get_orders_as_debtor,
    format_balances_for_view,
    calculate_balances,
)
from django.utils.timezone import now
from django.contrib import messages
from collections import defaultdict
from meal_together.emails import (
    send_invitation_email,
    send_order_update_email,
    send_session_update_email,
)
from collections import defaultdict

User = get_user_model()


@login_required
def session_list(request):
    user = request.user

    active_sessions = MealSession.objects.filter(
        participants=user, order_deadline__gte=now()
    ).order_by("order_deadline")
    past_sessions = MealSession.objects.filter(
        participants=user, order_deadline__lt=now()
    ).order_by("-order_deadline")

    user_orders = Order.objects.filter(user=user)

    session_orders = {order.session.id: order for order in user_orders}

    for session in active_sessions:
        session.user_expense = session.total_spent_by_user(user)
        session.order = session_orders.get(session.id)

    for session in past_sessions:
        session.user_expense = session.total_spent_by_user(user)
        session.order = session_orders.get(session.id)

    total_spent = sum(session.user_expense for session in active_sessions) + sum(
        session.user_expense for session in past_sessions
    )

    return render(
        request,
        "sessions/session_list.html",
        {
            "active_sessions": active_sessions,
            "past_sessions": past_sessions,
            "total_spent": total_spent,
        },
    )


@login_required
def create_session(request):
    if request.method == "POST":
        form = MealSessionForm(request.POST, user=request.user)
        if form.is_valid():
            session = form.save(commit=False)
            session.creator = request.user
            session.save()
            form.save_m2m()

            session.participants.add(request.user)

            invited_users = list(session.participants.all())

            selected_groups = form.cleaned_data.get("groups")
            if selected_groups:
                group_users = User.objects.filter(groups__in=selected_groups).distinct()
                session.participants.add(*group_users)
                invited_users.extend(group_users)

            invited_users = set(invited_users)

            current_site = get_current_site(request)

            send_invitation_email(current_site, invited_users, session)

            return redirect("session_list")
    else:
        form = MealSessionForm(user=request.user)
    return render(request, "sessions/create_session.html", {"form": form})


@login_required
def session_detail(request, session_id):
    session = get_object_or_404(MealSession, id=session_id)

    orders = session.orders.select_related("user").all()

    orders_by_user = defaultdict(list)
    for order in orders:
        orders_by_user[order.user.id].append(order)

    participants_data = process_participants(
        session, orders_by_user=orders_by_user, include_creator_info=True
    )

    participants_data.sort(key=lambda x: not x["is_creator"])

    context = {
        "session": session,
        "participants_data": participants_data,
        "is_creator": request.user == session.creator,
    }
    return render(request, "sessions/session_detail.html", context)


@login_required
def session_edit(request, session_id):
    session = get_object_or_404(MealSession, id=session_id)

    if request.user != session.creator:
        return redirect("session_detail", session_id=session.id)

    original_session = {
        "name": session.name,
        "restaurant": session.restaurant,
        "delivery_time": session.delivery_time,
        "order_deadline": session.order_deadline,
    }

    if request.method == "POST":
        form = MealSessionForm(request.POST, instance=session, user=request.user)
        if form.is_valid():
            updated_session = form.save(commit=False)

            changes = get_session_changes(original_session, updated_session)

            updated_session.save()
            form.save_m2m()
            session.participants.add(request.user)

            if changes:
                current_site = get_current_site(request)
                send_session_update_email(current_site, changes, session)

            return redirect("session_detail", session_id=session.id)
    else:
        form = MealSessionForm(instance=session, user=request.user)

    context = {
        "session": session,
        "form": form,
    }
    return render(request, "sessions/session_edit.html", context)


@login_required
def create_order(request, session_id, user_id=None):
    session = get_object_or_404(MealSession, id=session_id)
    user = (
        request.user
        if request.user.id == user_id
        else get_object_or_404(User, id=user_id)
    )

    if session.order_deadline < now() and request.user.id != session.creator.id:
        messages.error(
            request, "Order deadline has passed. You cannot create or edit orders."
        )
        return redirect("session_detail", session_id=session.id)

    order_exists = Order.objects.filter(session=session, user=user).exists()
    if order_exists:
        messages.error(request, "Order already exists. You can edit it.")
        return redirect("edit_order", session_id=session.id, user_id=user.id)

    order = Order(session=session, user=user)

    if request.method == "POST":
        order_form = OrderForm(request.POST, instance=order)
        formset = OrderItemFormSet(request.POST, instance=order)

        for form in formset.forms:
            form.fields['menu_item'].queryset = MenuItem.objects.filter(
                restaurant=session.restaurant
            )

        if order_form.is_valid() and formset.is_valid():
            order = order_form.save(commit=False)
            order.save()
            formset.instance = order
            formset.save()

            order.total_price = sum(
                item.menu_item.price * item.quantity
                for item in order.orderitem_set.all()
            )
            order.save()

            if request.user != user and request.user == session.creator:
                current_site = get_current_site(request).domain
                items_list = list(order.orderitem_set.all())
                send_order_update_email(current_site, items_list, order)

            messages.success(request, "Order has been created.")
            return redirect("session_detail", session_id=session.id)
    else:
        order_form = OrderForm(instance=order)
        formset = OrderItemFormSet(instance=order)

        for form in formset.forms:
            form.fields['menu_item'].queryset = MenuItem.objects.filter(
                restaurant=session.restaurant
            )

    return render(
        request,
        "sessions/create_order.html",
        {
            "session": session,
            "order": order,
            "order_form": order_form,
            "formset": formset,
            "user": user,
        },
    )


@login_required
def edit_order(request, session_id, user_id):
    session = get_object_or_404(MealSession, id=session_id)
    user = get_object_or_404(User, id=user_id)

    if request.user != user and request.user != session.creator:
        messages.error(request, "You do not have permission to edit this order.")
        return redirect("session_detail", session_id=session.id)

    if session.order_deadline < now() and request.user != session.creator:
        messages.error(
            request, "Order deadline has passed. You cannot create or edit orders."
        )
        return redirect("session_detail", session_id=session.id)

    order = get_object_or_404(Order, session=session, user=user)

    if "cancel_order" in request.POST:
        if request.user != user and request.user == session.creator:
            current_site = get_current_site(request).domain
            send_order_update_email(current_site, ["Order deleted"], order)
        order.delete()
        messages.success(request, "Order has been canceled.")
        return redirect("session_detail", session_id=session.id)

    original_order = Order.objects.get(pk=order.pk)
    original_items = list(order.orderitem_set.all())

    if request.method == "POST":
        order_form = OrderForm(request.POST, instance=order)
        formset = OrderItemFormSet(request.POST, instance=order)
        for form in formset.forms:
            form.fields['menu_item'].queryset = MenuItem.objects.filter(
                restaurant=session.restaurant
            )

        if order_form.is_valid() and formset.is_valid():
            updated_order = order_form.save(commit=False)

            formset.save()

            deleted_items = formset.deleted_objects
            updated_items = list(updated_order.orderitem_set.all())
            updated_order.total_price = sum(
                item.menu_item.price * item.quantity for item in updated_items
            )
            updated_order.save()

            changes = get_order_changes(
                original_order,
                updated_order,
                original_items,
                updated_items,
                deleted_items,
            )

            if changes and request.user != user and request.user == session.creator:
                current_site = get_current_site(request).domain
                send_order_update_email(current_site, changes, updated_order)

            messages.success(request, "Order has been saved.")
            return redirect("session_detail", session_id=session.id)
    else:
        order_form = OrderForm(instance=order)
        formset = OrderItemFormSet(instance=order)
        for form in formset.forms:
            form.fields['menu_item'].queryset = MenuItem.objects.filter(
                restaurant=session.restaurant
            )

    return render(
        request,
        "sessions/edit_order.html",
        {
            "session": session,
            "order": order,
            "order_form": order_form,
            "formset": formset,
            "user": user,
        },
    )


@login_required
def credit_balance_view(request):
    current_user = request.user
    orders_as_debtor = get_orders_as_debtor(current_user)
    orders_as_creditor = get_orders_as_creditor(current_user)
    balances = calculate_balances(orders_as_debtor, orders_as_creditor)
    total_balance = sum(balances.values())
    balances_list = format_balances_for_view(balances)
    context = {
        "balances": balances_list,
        "total_balance": total_balance,
    }
    return render(request, "sessions/credit_balance.html", context)


@login_required
def session_summary(request, session_id):
    session = get_object_or_404(MealSession, id=session_id)

    if request.user != session.creator:
        return render(
            request,
            "general/no_permission.html",
            {"message": "You do not have permission to view this summary."},
        )

    participant_orders = process_participants(session)

    aggregated_items = aggregate_order_items(session)

    total_session_spent = sum(value["total_price"] for value in aggregated_items)

    context = {
        "session": session,
        "participant_orders": participant_orders,
        "aggregated_items": aggregated_items,
        "total_session_spent": total_session_spent,
    }
    return render(request, "sessions/session_summary.html", context)
