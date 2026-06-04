from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.conf import settings
from django.db.models import F
import razorpay
import json
from .models import Order, OrderItem, OrderStatusHistory
from .cart import Cart
from apps.coupons.models import Coupon, CouponUsage
from apps.accounts.models import Address
from apps.shipping.models import ShippingMethod


def cart_view(request):
    cart = Cart(request)
    return render(request, "orders/cart.html", {"cart": cart})


def cart_drawer(request):
    """HTML partial for the slide-out mini-cart."""
    cart = Cart(request)
    in_cart_ids = {int(v["product_id"]) for v in cart.cart.values()}
    viewed_ids = request.session.get("recently_viewed", [])
    rail = []
    if viewed_ids:
        from apps.products.models import Product
        qs = Product.objects.filter(pk__in=viewed_ids, is_active=True).prefetch_related("images")
        by_id = {p.pk: p for p in qs}
        rail = [by_id[pid] for pid in viewed_ids if pid in by_id and pid not in in_cart_ids][:4]

    # Free-shipping progress meter
    from apps.core.models import SiteSettings
    from decimal import Decimal
    settings_obj = SiteSettings.get_settings()
    threshold = settings_obj.free_shipping_threshold or Decimal("0")
    subtotal = cart.total_after_bundle
    ship = {
        "threshold": threshold,
        "qualifies": threshold <= 0 or subtotal >= threshold,
        "remaining": max(Decimal("0"), threshold - subtotal),
        "percent": min(100, int(subtotal / threshold * 100)) if threshold > 0 else 100,
    }
    return render(request, "orders/_cart_drawer.html", {"cart": cart, "drawer_rail": rail, "ship": ship})


@login_required
def checkout_view(request):
    cart = Cart(request)
    if cart.is_empty():
        return redirect("products:list")
    addresses = Address.objects.filter(user=request.user)
    shipping_methods = ShippingMethod.objects.filter(is_active=True)
    from apps.accounts.services import MIN_REDEEM
    context = {
        "cart": cart,
        "addresses": addresses,
        "shipping_methods": shipping_methods,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "loyalty_points": request.user.loyalty_points,
        "min_redeem": MIN_REDEEM,
    }
    return render(request, "orders/checkout.html", context)


@login_required
@require_POST
def create_order(request):
    cart = Cart(request)
    if cart.is_empty():
        return JsonResponse({"success": False, "message": "Cart is empty"})
    # Re-validate stock at checkout (it may have sold out since being added)
    from apps.orders.inventory import check_availability
    for item in cart:
        ok, avail, msg = check_availability(item["product"], item.get("variant"), item["quantity"])
        if not ok:
            name = item["product"].name
            return JsonResponse({"success": False, "message": f"{name}: {msg or 'no longer available'}. Please update your bag."})
    data = json.loads(request.body)
    address_id = data.get("address_id")
    payment_method = data.get("payment_method", "razorpay")
    coupon_code = data.get("coupon_code", "")
    gift_message = data.get("gift_message", "")
    is_gift = data.get("is_gift", False)
    redeem = int(data.get("redeem_points", 0) or 0)
    try:
        address = Address.objects.get(pk=address_id, user=request.user)
    except Address.DoesNotExist:
        return JsonResponse({"success": False, "message": "Invalid address"})
    shipping_charge = 0
    shipping_method_id = data.get("shipping_method_id")
    if shipping_method_id:
        try:
            sm = ShippingMethod.objects.get(pk=shipping_method_id)
            shipping_charge = sm.calculate_price(cart.subtotal)
        except ShippingMethod.DoesNotExist:
            pass
    discount = 0
    coupon = None
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code.strip().upper())
            valid, _ = coupon.is_valid()
            if valid and cart.subtotal >= coupon.min_order_amount:
                discount = coupon.calculate_discount(cart.subtotal)
            else:
                coupon = None  # don't record usage if it didn't actually apply
        except Coupon.DoesNotExist:
            pass
    # Bundle & save — automatic discount for 3+ candles, stacks on top of coupons
    bundle_discount = cart.bundle_discount
    discount = discount + bundle_discount
    # Loyalty points redemption (1 point = Rs.1), capped so it never exceeds the order
    points_discount = 0
    from decimal import Decimal
    if redeem:
        from apps.accounts.services import MIN_REDEEM
        provisional = cart.subtotal + shipping_charge - discount
        max_points = min(redeem, request.user.loyalty_points, int(provisional))
        if max_points >= MIN_REDEEM:
            from apps.accounts.services import redeem_points
            points_discount = redeem_points(request.user, max_points)
            discount = discount + Decimal(str(points_discount))
    subtotal = cart.subtotal
    total = subtotal + shipping_charge - discount
    # Tax (configurable in Site Settings)
    tax_amount = Decimal("0.00")
    from apps.core.models import SiteSettings
    site = SiteSettings.get_settings()
    if site.tax_enabled and site.tax_percentage:
        rate = Decimal(str(site.tax_percentage)) / Decimal("100")
        taxable = subtotal - discount
        if site.prices_include_tax:
            # tax is embedded in the price — record the portion, total unchanged
            tax_amount = (taxable - (taxable / (Decimal("1") + rate))).quantize(Decimal("0.01"))
        else:
            tax_amount = (taxable * rate).quantize(Decimal("0.01"))
            total = total + tax_amount
    notes_parts = []
    if bundle_discount:
        notes_parts.append(f"Bundle saving ({cart.bundle_rate_percent}% off {len(cart)} candles): -Rs.{bundle_discount}")
    if points_discount:
        notes_parts.append(f"Loyalty points redeemed: -Rs.{points_discount}")
    order = Order.objects.create(
        user=request.user, payment_method=payment_method,
        shipping_full_name=address.full_name, shipping_phone=address.phone,
        shipping_address_line1=address.address_line1, shipping_address_line2=address.address_line2,
        shipping_city=address.city, shipping_state=address.state,
        shipping_pincode=address.pincode, shipping_country=address.country,
        subtotal=subtotal, shipping_charge=shipping_charge, discount=discount, tax=tax_amount, total=total,
        coupon_code=coupon_code.upper() if coupon_code else "",
        gift_message=gift_message, is_gift=is_gift,
        notes="; ".join(notes_parts),
    )
    for item in cart:
        pi = item["product"].primary_image
        variant = item.get("variant")
        variant_info = ""
        if variant:
            variant_info = variant.name + ": " + variant.value
        OrderItem.objects.create(
            order=order, product=item["product"], variant=variant,
            product_name=item["product"].name, variant_info=variant_info,
            price=item["price"], quantity=item["quantity"],
            product_image=request.build_absolute_uri(pi.image.url) if pi else "",
        )
    if coupon:
        CouponUsage.objects.create(coupon=coupon, user=request.user, order=order, discount_amount=discount)
        coupon.times_used += 1
        coupon.save(update_fields=["times_used"])
    OrderStatusHistory.objects.create(order=order, status="pending", created_by=request.user)
    if payment_method == "razorpay":
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            rp_order = client.order.create({"amount": int(total * 100), "currency": "INR", "receipt": order.order_number})
            order.razorpay_order_id = rp_order["id"]
            order.save(update_fields=["razorpay_order_id"])
            return JsonResponse({
                "success": True, "order_id": order.pk,
                "razorpay_order_id": rp_order["id"], "amount": int(total * 100),
                "key": settings.RAZORPAY_KEY_ID,
                "name": order.shipping_full_name, "email": request.user.email,
            })
        except Exception as e:
            # Roll back everything we committed before payment could start
            if coupon:
                Coupon.objects.filter(pk=coupon.pk).update(times_used=F("times_used") - 1)
            if points_discount:
                from apps.accounts.services import refund_points
                refund_points(request.user, points_discount, order=None)
            order.delete()  # cascades OrderItems + CouponUsage
            return JsonResponse({"success": False, "message": "Could not start payment. Please try again."})
    elif payment_method == "cod":
        order.status = "confirmed"
        order.save(update_fields=["status"])
        cart.clear()
        request.user.cart_items.all().delete()
        return JsonResponse({"success": True, "order_id": order.pk, "redirect": "/orders/" + str(order.pk) + "/?placed=1"})
    return JsonResponse({"success": False})


@login_required
@require_POST
def verify_payment(request):
    data = json.loads(request.body)
    rzp_order_id = data.get("razorpay_order_id")
    rzp_payment_id = data.get("razorpay_payment_id")
    rzp_signature = data.get("razorpay_signature")
    try:
        order = Order.objects.get(razorpay_order_id=rzp_order_id, user=request.user)
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        client.utility.verify_payment_signature({
            "razorpay_order_id": rzp_order_id,
            "razorpay_payment_id": rzp_payment_id,
            "razorpay_signature": rzp_signature,
        })
        order.razorpay_payment_id = rzp_payment_id
        order.razorpay_signature = rzp_signature
        order.payment_status = "paid"
        order.status = "confirmed"
        order.save(update_fields=["razorpay_payment_id", "razorpay_signature", "payment_status", "status"])
        OrderStatusHistory.objects.create(order=order, status="confirmed")
        Cart(request).clear()
        request.user.cart_items.all().delete()
        return JsonResponse({"success": True, "order_id": order.pk, "redirect": "/orders/" + str(order.pk) + "/?placed=1"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items")
    return render(request, "orders/order_list.html", {"orders": orders})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return_request = order.return_requests.order_by("-created_at").first()
    return render(request, "orders/order_detail.html", {"order": order, "return_request": return_request})


@login_required
def order_invoice(request, pk):
    """Downloadable PDF invoice — accessible to the order's owner or any staff member."""
    if request.user.is_staff:
        order = get_object_or_404(Order, pk=pk)
    else:
        order = get_object_or_404(Order, pk=pk, user=request.user)

    from django.template.loader import render_to_string
    from apps.core.models import SiteSettings
    html = render_to_string("orders/invoice.html", {"order": order, "site": SiteSettings.get_settings()})

    try:
        from xhtml2pdf import pisa
        import io
        buf = io.BytesIO()
        result = pisa.CreatePDF(io.StringIO(html), dest=buf)
        if not result.err:
            from django.http import HttpResponse
            resp = HttpResponse(buf.getvalue(), content_type="application/pdf")
            resp["Content-Disposition"] = f'attachment; filename="AuraArchives-Invoice-{order.order_number}.pdf"'
            return resp
    except Exception as e:
        print(f"Invoice PDF error: {e}")

    # Fallback: render the printable HTML if PDF generation is unavailable
    from django.http import HttpResponse
    return HttpResponse(html)


@login_required
@require_POST
def request_return(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if not order.can_return():
        return JsonResponse({"success": False, "message": "This order isn't eligible for a return."})
    from .models import ReturnRequest
    if ReturnRequest.objects.filter(order=order, status__in=["pending", "approved"]).exists():
        return JsonResponse({"success": False, "message": "A return request for this order is already in progress."})
    data = json.loads(request.body)
    reason = data.get("reason", "other")
    description = (data.get("description") or "").strip()
    if not description:
        return JsonResponse({"success": False, "message": "Please tell us a little about the issue."})
    order.status = "refund_requested"
    order.save(update_fields=["status"])
    OrderStatusHistory.objects.create(order=order, status="refund_requested", note="Return requested by customer", created_by=request.user)
    ReturnRequest.objects.create(order=order, user=request.user, reason=reason, description=description)
    return JsonResponse({"success": True, "message": "Return requested — we'll review it within 24 hours."})


@login_required
@require_POST
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if order.can_cancel():
        order.status = "cancelled"
        order.save(update_fields=["status"])
        OrderStatusHistory.objects.create(order=order, status="cancelled", created_by=request.user)
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "message": "Order cannot be cancelled"})


@login_required
def apply_coupon(request):
    if request.method == "POST":
        from decimal import Decimal, InvalidOperation
        data = json.loads(request.body)
        code = data.get("code", "").strip().upper()
        if not code:
            return JsonResponse({"success": False, "message": "Please enter a coupon code"})
        try:
            cart_total = Decimal(str(data.get("cart_total", 0)))
        except (InvalidOperation, TypeError):
            cart_total = Decimal("0")
        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return JsonResponse({"success": False, "message": "That code isn't valid"})
        valid, msg = coupon.is_valid()
        if not valid:
            return JsonResponse({"success": False, "message": msg})
        if cart_total < coupon.min_order_amount:
            return JsonResponse({"success": False, "message": f"Spend ₹{coupon.min_order_amount:g}+ to use this code"})
        discount = float(coupon.calculate_discount(cart_total))
        return JsonResponse({"success": True, "discount": discount, "message": f"'{code}' applied — you saved ₹{discount:g}"})
    return JsonResponse({"success": False}, status=400)
