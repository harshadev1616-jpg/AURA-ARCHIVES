from django.db import transaction
from django.db.models import F

POINTS_PER_RUPEE = 0.1   # 10% back in points
RUPEE_PER_POINT = 1
MIN_REDEEM = 100
REFERRAL_BONUS = 100     # points to both referrer and new friend on first delivery


def _user_model():
    """Return the real User class (request.user may be a SimpleLazyObject)."""
    from .models import User
    return User


def award_points_for_order(order):
    """Grant loyalty points once an order is delivered. Idempotent per order."""
    from .models import LoyaltyTransaction
    User = _user_model()
    if not order.user:
        return 0
    if LoyaltyTransaction.objects.filter(order=order, points__gt=0).exists():
        return 0
    points = int(float(order.total) * POINTS_PER_RUPEE)
    if points <= 0:
        return 0
    with transaction.atomic():
        LoyaltyTransaction.objects.create(
            user=order.user, points=points,
            reason=f"Earned on order #{order.order_number}", order=order,
        )
        User.objects.filter(pk=order.user.pk).update(
            loyalty_points=F('loyalty_points') + points
        )
    return points


def redeem_points(user, points, order=None):
    """Redeem points for a rupee discount. Returns the discount amount."""
    from .models import LoyaltyTransaction
    User = _user_model()
    points = int(points)
    if points < MIN_REDEEM:
        return 0
    if points > user.loyalty_points:
        points = user.loyalty_points
    if points < MIN_REDEEM:
        return 0
    with transaction.atomic():
        LoyaltyTransaction.objects.create(
            user=user, points=-points,
            reason="Redeemed for discount", order=order,
        )
        User.objects.filter(pk=user.pk).update(
            loyalty_points=F('loyalty_points') - points
        )
    return points * RUPEE_PER_POINT


def refund_points(user, amount, order=None):
    """Restore previously-redeemed points (e.g. if an order failed before payment)."""
    from .models import LoyaltyTransaction
    User = _user_model()
    points = int(amount)
    if points <= 0:
        return 0
    with transaction.atomic():
        LoyaltyTransaction.objects.create(
            user=user, points=points,
            reason="Refund — order not completed", order=order,
        )
        User.objects.filter(pk=user.pk).update(
            loyalty_points=F('loyalty_points') + points
        )
    return points


def reward_referral_if_due(order):
    """On a referred user's first delivered order, award both parties REFERRAL_BONUS points."""
    from .models import LoyaltyTransaction
    User = _user_model()
    user = order.user
    if not user or user.referral_rewarded or not user.referred_by:
        return False
    referrer = user.referred_by
    with transaction.atomic():
        LoyaltyTransaction.objects.create(user=user, points=REFERRAL_BONUS,
            reason=f"Welcome bonus — referred by {referrer.first_name}", order=order)
        User.objects.filter(pk=user.pk).update(
            loyalty_points=F('loyalty_points') + REFERRAL_BONUS, referral_rewarded=True)
        LoyaltyTransaction.objects.create(user=referrer, points=REFERRAL_BONUS,
            reason=f"Referral reward — {user.first_name} placed their first order", order=order)
        User.objects.filter(pk=referrer.pk).update(
            loyalty_points=F('loyalty_points') + REFERRAL_BONUS)
    return True
