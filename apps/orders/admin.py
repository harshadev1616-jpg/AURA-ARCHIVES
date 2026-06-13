import csv

from django.contrib import admin, messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.html import format_html
from rangefilter.filters import DateRangeFilter

from .models import Order, OrderItem, OrderStatusHistory, ReturnRequest


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product", "product_name", "variant_info", "price", "quantity", "line_total"]
    can_delete = False


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ["status", "note", "created_by", "created_at"]
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "order_number",
        "user",
        "items_summary",
        "status_badge",
        "payment_status",
        "total",
        "tracking_number",
        "courier_name",
        "created_at",
        "invoice_link",
    ]
    list_editable = ["tracking_number", "courier_name"]
    list_filter = ["status", "payment_status", "payment_method", ("created_at", DateRangeFilter)]
    date_hierarchy = "created_at"
    search_fields = ["order_number", "user__email", "shipping_full_name", "shipping_phone", "items__product_name"]
    readonly_fields = ["order_number", "razorpay_order_id", "razorpay_payment_id", "created_at", "updated_at", "invoice_button", "address_label_button"]
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    fieldsets = (
        ("Order Info", {"fields": ("order_number", ("invoice_button", "address_label_button"), "user", "status", "payment_status", "payment_method")}),
        ("Payment", {"fields": ("razorpay_order_id", "razorpay_payment_id")}),
        ("Shipping Address", {"fields": ("shipping_full_name", "shipping_phone", "shipping_address_line1", "shipping_address_line2", "shipping_city", "shipping_state", "shipping_pincode", "shipping_country")}),
        ("Amounts", {"fields": ("subtotal", "shipping_charge", "discount", "tax", "total", "coupon_code")}),
        ("Tracking", {"fields": ("tracking_number", "courier_name", "tracking_url", "estimated_delivery", "delivered_at")}),
        ("Gift", {"fields": ("is_gift", "gift_message")}),
    )

    def status_badge(self, obj):
        colors = {
            "pending": "#f59e0b",
            "confirmed": "#3b82f6",
            "processing": "#8b5cf6",
            "shipped": "#06b6d4",
            "delivered": "#10b981",
            "cancelled": "#ef4444",
            "refunded": "#6b7280",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            "<span style='background:{};color:white;padding:2px 8px;border-radius:12px;font-size:11px'>{}</span>",
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    def items_summary(self, obj):
        items = list(obj.items.all()[:3])
        if not items:
            return "-"
        text = ", ".join(f"{item.product_name} x{item.quantity}" for item in items)
        extra = obj.items.count() - len(items)
        if extra > 0:
            text += f" +{extra} more"
        return text

    items_summary.short_description = "Products"

    def invoice_link(self, obj):
        return format_html(
            '<a href="/orders/{}/invoice/" target="_blank" style="color:#B8945A;font-weight:600">Download invoice</a>',
            obj.pk,
        )

    invoice_link.short_description = "Invoice"

    def invoice_button(self, obj):
        if not obj.pk:
            return "-"
        return format_html(
            '<a class="button" href="/orders/{}/invoice/" target="_blank" '
            'style="background:#2B2B2B;color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none">Download invoice (PDF)</a>',
            obj.pk,
        )

    invoice_button.short_description = "Invoice"

    def address_label_button(self, obj):
        if not obj.pk:
            return "-"
        return format_html(
            '<a class="button" href="/orders/{}/label/" target="_blank" '
            'style="background:#B8945A;color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none">'
            'Download address label (PDF)</a>',
            obj.pk,
        )

    address_label_button.short_description = "Address label"

    actions = [
        "ship_with_tracking",
        "address_labels",
        "packing_slips",
        "mark_confirmed",
        "mark_processing",
        "mark_shipped",
        "mark_out_for_delivery",
        "mark_delivered",
        "mark_cancelled",
        "export_orders_csv",
    ]

    @admin.action(description="Ship with tracking")
    def ship_with_tracking(self, request, queryset):
        if "apply" in request.POST:
            courier = request.POST.get("courier_name", "").strip()
            est = request.POST.get("estimated_delivery", "").strip() or None
            shipped = 0
            for order in queryset:
                tracking = request.POST.get(f"tracking_{order.pk}", "").strip()
                order.tracking_number = tracking
                order.courier_name = courier
                if tracking and courier:
                    order.tracking_url = f"https://www.google.com/search?q={courier}+{tracking}"
                if est:
                    order.estimated_delivery = est
                order.status = "shipped"
                order.save()
                OrderStatusHistory.objects.create(
                    order=order,
                    status="shipped",
                    note=f"Shipped via {courier} {tracking}".strip(),
                    created_by=request.user,
                )
                shipped += 1
            self.message_user(
                request,
                f"{shipped} order(s) marked shipped with tracking. Customers emailed.",
                messages.SUCCESS,
            )
            return None
        return render(
            request,
            "admin/ship_with_tracking.html",
            {
                "orders": queryset,
                "action_checkbox_name": ACTION_CHECKBOX_NAME,
                "title": "Ship orders with tracking",
            },
        )

    @admin.action(description="Download address labels (PDF) — paste on packages")
    def address_labels(self, request, queryset):
        from .pdf_utils import generate_shipping_labels_pdf

        pdf_buffer = generate_shipping_labels_pdf(queryset)
        if pdf_buffer:
            response = HttpResponse(pdf_buffer.getvalue(), content_type="application/pdf")
            response["Content-Disposition"] = 'attachment; filename="aura-address-labels.pdf"'
            return response
        self.message_user(request, "Could not generate address labels.", level=messages.ERROR)

    @admin.action(description="Download packing slips (PDF)")
    def packing_slips(self, request, queryset):
        from .pdf_utils import generate_packing_slip_pdf

        pdf_buffer = generate_packing_slip_pdf(queryset)

        if pdf_buffer:
            response = HttpResponse(pdf_buffer.getvalue(), content_type="application/pdf")
            response["Content-Disposition"] = 'attachment; filename="aura-packing-slips.pdf"'
            return response

        html = render_to_string("orders/packing_slip.html", {"orders": queryset})
        return HttpResponse(html)

    def _bulk_status(self, request, queryset, new_status, verb):
        """Apply a status to each order via save() so signals fire."""
        updated = 0
        for order in queryset:
            if order.status != new_status:
                order.status = new_status
                order.save()
                OrderStatusHistory.objects.create(order=order, status=new_status, created_by=request.user)
                updated += 1
        self.message_user(request, f"{updated} order(s) marked {verb}. Customers notified where applicable.")

    @admin.action(description="Mark confirmed")
    def mark_confirmed(self, request, qs):
        self._bulk_status(request, qs, "confirmed", "confirmed")

    @admin.action(description="Mark processing")
    def mark_processing(self, request, qs):
        self._bulk_status(request, qs, "processing", "processing")

    @admin.action(description="Mark shipped")
    def mark_shipped(self, request, qs):
        self._bulk_status(request, qs, "shipped", "shipped")

    @admin.action(description="Mark out for delivery")
    def mark_out_for_delivery(self, request, qs):
        self._bulk_status(request, qs, "out_for_delivery", "out for delivery")

    @admin.action(description="Mark delivered")
    def mark_delivered(self, request, qs):
        self._bulk_status(request, qs, "delivered", "delivered")

    @admin.action(description="Mark cancelled")
    def mark_cancelled(self, request, qs):
        self._bulk_status(request, qs, "cancelled", "cancelled")

    @admin.action(description="Export selected orders to CSV")
    def export_orders_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="aura-orders.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "Order",
                "Date",
                "Customer",
                "Email",
                "Phone",
                "Status",
                "Payment",
                "Method",
                "Subtotal",
                "Discount",
                "Tax",
                "Shipping",
                "Total",
                "Items",
                "City",
                "Pincode",
            ]
        )
        for order in queryset.select_related("user").prefetch_related("items"):
            items = " | ".join(f"{item.product_name} x{item.quantity}" for item in order.items.all())
            writer.writerow(
                [
                    order.order_number,
                    order.created_at.strftime("%Y-%m-%d %H:%M"),
                    order.shipping_full_name,
                    order.user.email if order.user else "",
                    order.shipping_phone,
                    order.get_status_display(),
                    order.get_payment_status_display(),
                    order.get_payment_method_display(),
                    order.subtotal,
                    order.discount,
                    order.tax,
                    order.shipping_charge,
                    order.total,
                    items,
                    order.shipping_city,
                    order.shipping_pincode,
                ]
            )
        self.message_user(request, f"Exported {queryset.count()} order(s).")
        return response

    def save_model(self, request, obj, form, change):
        if change:
            old = Order.objects.get(pk=obj.pk)
            super().save_model(request, obj, form, change)
            if old.status != obj.status:
                OrderStatusHistory.objects.create(order=obj, status=obj.status, created_by=request.user)
        else:
            super().save_model(request, obj, form, change)


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ["order_link", "user", "reason", "status_badge", "refund_amount", "created_at"]
    list_filter = ["status", "reason"]
    search_fields = ["order__order_number", "user__email"]
    readonly_fields = ["order", "user", "reason", "description", "created_at"]
    actions = ["approve_and_refund", "reject_return"]
    fieldsets = (
        ("Request", {"fields": ("order", "user", "reason", "description", "created_at")}),
        (
            "Decision",
            {
                "fields": ("status", "refund_amount", "admin_note"),
                "description": "Use the <b>Approve &amp; refund</b> action to refund, restock, and notify the customer in one step.",
            },
        ),
    )

    def order_link(self, obj):
        return format_html('<a href="/aura-admin/orders/order/{}/change/">#{}</a>', obj.order_id, obj.order.order_number)

    order_link.short_description = "Order"

    def status_badge(self, obj):
        colors = {"pending": "#f59e0b", "approved": "#10b981", "rejected": "#ef4444", "completed": "#6b7280"}
        return format_html(
            "<span style='background:{};color:white;padding:2px 8px;border-radius:12px;font-size:11px'>{}</span>",
            colors.get(obj.status, "#6b7280"),
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    @admin.action(description="Approve and refund")
    def approve_and_refund(self, request, queryset):
        done = 0
        for return_request in queryset.filter(status="pending"):
            order = return_request.order
            amount = return_request.refund_amount or order.total
            if order.razorpay_payment_id:
                try:
                    import razorpay
                    from django.conf import settings

                    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                    client.payment.refund(order.razorpay_payment_id, {"amount": int(float(amount) * 100)})
                except Exception as exc:
                    self.message_user(
                        request,
                        f"#{order.order_number}: Razorpay refund not processed ({exc}). Marked refunded; issue manually if needed.",
                        level="warning",
                    )
            return_request.status = "approved"
            return_request.refund_amount = amount
            return_request.save(update_fields=["status", "refund_amount"])
            order.payment_status = "refunded"
            order.status = "returned"
            order.save()
            OrderStatusHistory.objects.create(
                order=order,
                status="returned",
                note=f"Return approved - refund Rs.{amount}",
                created_by=request.user,
            )
            try:
                from apps.notifications.services import notify_return_update

                notify_return_update(return_request, "approved", amount)
            except Exception:
                pass
            done += 1
        self.message_user(request, f"{done} return(s) approved, refunded & restocked.")

    @admin.action(description="Reject return")
    def reject_return(self, request, queryset):
        done = 0
        for return_request in queryset.filter(status="pending"):
            return_request.status = "rejected"
            return_request.save(update_fields=["status"])
            return_request.order.status = "delivered"
            return_request.order.save(update_fields=["status"])
            try:
                from apps.notifications.services import notify_return_update

                notify_return_update(return_request, "rejected", None)
            except Exception:
                pass
            done += 1
        self.message_user(request, f"{done} return(s) rejected.")
