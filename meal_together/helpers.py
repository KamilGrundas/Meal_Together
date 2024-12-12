from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.db.models import QuerySet, Sum
from meal_together.models.sessions import MealSession, Order, OrderItem
from six import text_type
from typing import List, Dict, Union, Any
from collections import defaultdict
from django.contrib.auth import get_user_model

User = get_user_model()


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return text_type(user.pk) + text_type(timestamp) + text_type(user.is_active)


account_activation_token = AccountActivationTokenGenerator()


def get_session_changes(
    original_session: MealSession, updated_session: MealSession
) -> List[str]:
    changes = []

    # Iterate over fields in the original session to check for changes
    for field, old_value in original_session.items():
        new_value = getattr(updated_session, field)

        # If the value has changed, append the change to the list
        if old_value != new_value:
            # Handle restaurant field separately
            if field == "restaurant":
                changes.append(f"Restaurant: {old_value.name} -> {new_value.name}")

            # Handle fields related to time (delivery_time, order_deadline)
            elif field in ["delivery_time", "order_deadline"]:
                changes.append(
                    f"{field.replace('_', ' ').capitalize()}: from {old_value.strftime('%H:%M')} to {new_value.strftime('%H:%M')}"
                )
            else:
                # Handle all other fields
                changes.append(
                    f"{field.replace('_', ' ').capitalize()}: from {old_value} to {new_value}"
                )

    return changes


def get_order_changes(
    original_order: Order,
    updated_order: Order,
    original_items: List,
    updated_items: List,
    deleted_items: List,
) -> List[str]:
    changes = []

    # Helper function to check for changes in a specific field of the order
    def check_field_change(field: str) -> None:
        old_value = getattr(original_order, field)
        new_value = getattr(updated_order, field)
        if old_value != new_value:
            changes.append(
                f"{field.replace('_', ' ').capitalize()}: {old_value} -> {new_value}"
            )

    # Check for changes in the payment method
    check_field_change("payment_method")

    # Create dictionaries for easy comparison of order items
    original_items_dict = {item.id: item for item in original_items}
    updated_items_dict = {item.id: item for item in updated_items}

    # Identify new and removed item IDs
    new_item_ids = set(updated_items_dict) - set(original_items_dict)
    removed_ids = set(original_items_dict) - set(updated_items_dict)

    # Add changes for removed items from the original order
    changes.extend(
        [
            f"Removed item: {item.menu_item.name} x{item.quantity}"
            for item_id in removed_ids
            for item in [original_items_dict[item_id]]
        ]
    )

    # Add changes for removed items that are explicitly deleted
    changes.extend(
        [
            f"Removed item: {item.menu_item.name} x{item.quantity}"
            for item in deleted_items
        ]
    )

    # Add changes for new items in the updated order
    changes.extend(
        [
            f"Added item: {item.menu_item.name} x{item.quantity}"
            for item_id in new_item_ids
            for item in [updated_items_dict[item_id]]
        ]
    )

    # Check for changes in common items (those that are present in both original and updated orders)
    common_ids = set(original_items_dict) & set(updated_items_dict)
    for item_id in common_ids:
        original_item = original_items_dict[item_id]
        updated_item = updated_items_dict[item_id]

        item_changes = []

        # Check for changes in the menu item
        if original_item.menu_item != updated_item.menu_item:
            item_changes.append(
                f"Menu item changed from {original_item.menu_item.name} to {updated_item.menu_item.name}"
            )

        # Check for changes in the quantity
        if original_item.quantity != updated_item.quantity:
            item_changes.append(
                f"Quantity changed from {original_item.quantity} to {updated_item.quantity}"
            )

        # Check for changes in the note
        if (original_item.note or "") != (updated_item.note or ""):
            old_note = original_item.note or ""
            new_note = updated_item.note or ""
            item_changes.append(f"Note changed from '{old_note}' to '{new_note}'")

        # Add changes for this item if any changes were detected
        if item_changes:
            changes.append(
                f"Updated item ({original_item.menu_item.name}): "
                + "; ".join(item_changes)
            )

    return changes


def process_participants(
    session, orders_by_user=None, include_creator_info=False
) -> List[Dict[str, Union[Any, List[Any], float, bool]]]:
    participants_data = []

    for participant in session.participants.all():
        # Fetch orders based on whether orders_by_user is provided
        user_orders = (
            orders_by_user.get(participant.id, [])
            if orders_by_user
            else participant.orders.filter(session=session)
        )
        total_spent = sum(order.total_price for order in user_orders)
        items = []
        payment_methods = []

        # If orders_by_user is not provided, fetch items from orders
        if not orders_by_user:
            for order in user_orders:
                items.extend(order.orderitem_set.all())
        else:
            # Collect unique payment methods
            payment_methods = list(set(order.payment_method for order in user_orders))

        # Base participant data
        participant_data = {
            "user": participant,
            "total_spent": total_spent,
            "orders": user_orders,
        }

        # Add additional details if applicable
        if not orders_by_user:
            participant_data["items"] = items
        if include_creator_info:
            participant_data["is_creator"] = participant == session.creator
            participant_data["payment_methods"] = payment_methods

        participants_data.append(participant_data)

    return participants_data


def aggregate_order_items(
    session: MealSession,
) -> List[Dict[str, Union[str, int, float]]]:
    """
    Aggregate all order items in the session by item name.
    """
    aggregated_items = defaultdict(lambda: {"quantity": 0, "total_price": 0})
    all_order_items = OrderItem.objects.filter(order__session=session)
    for item in all_order_items:
        key = item.menu_item.name
        aggregated_items[key]["quantity"] += item.quantity
        aggregated_items[key]["total_price"] += item.menu_item.price * item.quantity

    # Convert the aggregated dictionary to a list
    return [
        {
            "name": key,
            "quantity": value["quantity"],
            "total_price": value["total_price"],
        }
        for key, value in aggregated_items.items()
    ]


def get_orders_as_debtor(user) -> QuerySet:
    return Order.objects.filter(user=user, payment_method="Credit").exclude(
        session__creator=user
    )


def get_orders_as_creditor(user) -> QuerySet:
    return Order.objects.filter(session__creator=user, payment_method="Credit").exclude(
        user=user
    )


def calculate_balances(
    orders_as_debtor: QuerySet, orders_as_creditor: QuerySet
) -> Dict[int, float]:
    balances = {}
    users_current_user_owes = orders_as_debtor.values("session__creator").annotate(
        total_owed=Sum("total_price")
    )
    for item in users_current_user_owes:
        user_id = item["session__creator"]
        amount = item["total_owed"]
        balances[user_id] = balances.get(user_id, 0) + amount

    users_who_owe_current_user = orders_as_creditor.values("user").annotate(
        total_owed=Sum("total_price")
    )
    for item in users_who_owe_current_user:
        user_id = item["user"]
        amount = item["total_owed"]
        balances[user_id] = balances.get(user_id, 0) - amount

    return balances


def format_balances_for_view(balances: Dict[int, float]) -> List:
    balances_list = []
    for user_id, balance in balances.items():
        if balance != 0:
            user = User.objects.get(pk=user_id)
            balances_list.append({"user": user, "balance": balance})
    return balances_list
