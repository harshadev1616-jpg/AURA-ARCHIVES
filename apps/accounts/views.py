from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .models import User, Address
from .forms import UserRegistrationForm, UserLoginForm, ProfileUpdateForm, AddressForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = UserLoginForm(data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        next_url = request.GET.get("next", "accounts:dashboard")
        return redirect(next_url)
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("/")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    # Capture referral code from the link or a previously-stored session value
    ref_code = request.GET.get("ref") or request.session.get("ref_code")
    if request.GET.get("ref"):
        request.session["ref_code"] = request.GET["ref"]
    form = UserRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        ref_code = request.POST.get("ref_code") or request.session.get("ref_code")
        if ref_code:
            referrer = User.objects.filter(referral_code=ref_code.strip().upper()).exclude(pk=user.pk).first()
            if referrer:
                user.referred_by = referrer
                user.save(update_fields=["referred_by"])
                request.session.pop("ref_code", None)
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, "Welcome to Aura Archives!")
        return redirect("accounts:dashboard")
    return render(request, "accounts/register.html", {"form": form, "ref_code": ref_code or ""})


@login_required
def dashboard(request):
    from apps.orders.models import Order
    recent_orders = Order.objects.filter(user=request.user).prefetch_related("items")[:5]
    from apps.notifications.models import Notification
    unread_notifs = Notification.objects.filter(user=request.user, is_read=False).count()
    loyalty_history = request.user.loyalty_transactions.all()[:8]
    from apps.accounts.services import RUPEE_PER_POINT, MIN_REDEEM
    return render(request, "accounts/dashboard.html", {
        "recent_orders": recent_orders,
        "unread_notifications": unread_notifs,
        "loyalty_history": loyalty_history,
        "loyalty_value": request.user.loyalty_points * RUPEE_PER_POINT,
        "min_redeem": MIN_REDEEM,
    })


@login_required
def profile(request):
    form = ProfileUpdateForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated!")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form})


@login_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, "accounts/addresses.html", {"addresses": addresses})


@login_required
def address_add(request):
    form = AddressForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        address = form.save(commit=False)
        address.user = request.user
        address.save()
        messages.success(request, "Address added!")
        return redirect("accounts:addresses")
    return render(request, "accounts/address_form.html", {"form": form, "title": "Add Address"})


@login_required
def address_edit(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    form = AddressForm(request.POST or None, instance=address)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Address updated!")
        return redirect("accounts:addresses")
    return render(request, "accounts/address_form.html", {"form": form, "title": "Edit Address"})


@login_required
@require_POST
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    return JsonResponse({"success": True})


@login_required
def wishlist_view(request):
    from apps.wishlist.models import Wishlist
    wishlist = Wishlist.objects.get_or_create(user=request.user)[0]
    return render(request, "accounts/wishlist.html", {"wishlist": wishlist})


@login_required
def notifications(request):
    from apps.notifications.models import Notification
    notifs = Notification.objects.filter(user=request.user)
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, "accounts/notifications.html", {"notifications": notifs})
