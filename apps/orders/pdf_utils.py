"""
PDF generation utilities using reportlab (Vercel-compatible).
Converts HTML invoice and packing slip data to PDF using reportlab.
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.pdfgen import canvas


def html_to_plain_text(html_content):
    """
    Basic HTML stripper for reportlab.
    Removes common HTML tags to get plain text.
    """
    import re
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html_content)
    # Decode HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    return text.strip()


def generate_invoice_pdf(order, site_settings):
    """
    Generate a PDF invoice using reportlab.
    
    Args:
        order: Order object
        site_settings: SiteSettings object
    
    Returns:
        BytesIO object with PDF content or None if generation fails
    """
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#333333'),
            spaceAfter=30,
            alignment=1,  # center
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#C9A86A'),
            spaceAfter=12,
        )
        normal_style = styles['Normal']
        
        # Title
        elements.append(Paragraph("INVOICE", title_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Header info
        header_data = [
            [f"Invoice #: {order.order_number}", f"Date: {order.created_at.strftime('%Y-%m-%d')}"],
            [f"Status: {order.status.upper()}", f"Amount: ₹{order.total:.2f}"],
        ]
        header_table = Table(header_data, colWidths=[3 * inch, 3 * inch])
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Customer info
        elements.append(Paragraph("CUSTOMER INFORMATION", heading_style))
        customer_data = [
            [f"Name: {order.user.get_full_name() or order.user.email}"],
            [f"Email: {order.user.email}"],
            [f"Phone: {order.user.profile.phone_number if hasattr(order.user, 'profile') else 'N/A'}"],
        ]
        customer_table = Table(customer_data, colWidths=[5.5 * inch])
        customer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(customer_table)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Order items
        elements.append(Paragraph("ORDER ITEMS", heading_style))
        items_data = [['Product', 'Quantity', 'Price', 'Total']]
        for item in order.items.all():
            items_data.append([
                item.product.name[:30],
                str(item.quantity),
                f"₹{item.price:.2f}",
                f"₹{item.total_price:.2f}",
            ])
        
        items_table = Table(items_data, colWidths=[2.5 * inch, 1 * inch, 1 * inch, 1 * inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C9A86A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Summary
        summary_data = [
            ['Subtotal:', f"₹{order.subtotal:.2f}"],
            ['Shipping:', f"₹{order.shipping_cost:.2f}"],
            ['Tax:', f"₹{order.tax_amount:.2f}"],
            ['Discount:', f"₹{order.discount_amount:.2f}"],
            ['TOTAL:', f"₹{order.total:.2f}"],
        ]
        summary_table = Table(summary_data, colWidths=[3 * inch, 2.5 * inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#D8D0E8')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(summary_table)
        
        # Footer
        elements.append(Spacer(1, 0.3 * inch))
        if site_settings:
            elements.append(Paragraph(
                f"Thank you for your purchase! For support, contact {site_settings.support_email or 'support@example.com'}",
                ParagraphStyle('footer', parent=styles['Normal'], fontSize=8, alignment=1)
            ))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"Error generating PDF invoice: {e}")
        return None


def generate_packing_slip_pdf(orders):
    """
    Generate a PDF packing slip for multiple orders using reportlab.
    
    Args:
        orders: QuerySet of Order objects
    
    Returns:
        BytesIO object with PDF content or None if generation fails
    """
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#333333'),
            spaceAfter=20,
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=colors.HexColor('#C9A86A'),
            spaceAfter=10,
        )
        
        for i, order in enumerate(orders):
            if i > 0:
                elements.append(PageBreak())
            
            # Title
            elements.append(Paragraph(f"PACKING SLIP - Order #{order.order_number}", title_style))
            
            # Order info
            elements.append(Paragraph("ORDER DETAILS", heading_style))
            order_data = [
                [f"Order #: {order.order_number}", f"Date: {order.created_at.strftime('%Y-%m-%d')}"],
                [f"Status: {order.status.upper()}", f"Total: ₹{order.total:.2f}"],
            ]
            order_table = Table(order_data, colWidths=[3 * inch, 3 * inch])
            order_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(order_table)
            elements.append(Spacer(1, 0.15 * inch))
            
            # Items to pack
            elements.append(Paragraph("ITEMS TO PACK", heading_style))
            items_data = [['SKU', 'Product', 'Quantity', 'Notes']]
            for item in order.items.all():
                is_fragile = 'Fragile' if (hasattr(item.product, 'is_fragile') and item.product.is_fragile) else ''
                items_data.append([
                    getattr(item.product, 'sku', '-'),
                    item.product.name[:25],
                    str(item.quantity),
                    is_fragile,
                ])
            
            items_table = Table(items_data, colWidths=[1.2 * inch, 2.5 * inch, 1 * inch, 1.3 * inch])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C9A86A')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            elements.append(items_table)
            elements.append(Spacer(1, 0.15 * inch))
            
            # Shipping info (Order stores a flat shipping address)
            elements.append(Paragraph("SHIPPING ADDRESS", heading_style))
            addr_bits = [order.shipping_full_name, order.shipping_address_line1]
            if order.shipping_address_line2:
                addr_bits.append(order.shipping_address_line2)
            addr_bits.append(f"{order.shipping_city}, {order.shipping_state} - {order.shipping_pincode}")
            addr_bits.append(order.shipping_country)
            addr_bits.append(f"Phone: {order.shipping_phone}")
            elements.append(Paragraph("<br/>".join(b for b in addr_bits if b), styles['Normal']))
            elements.append(Spacer(1, 0.2 * inch))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"Error generating packing slip PDF: {e}")
        return None


def generate_shipping_labels_pdf(orders):
    """Printable address labels to paste on the package — one per order/page.

    Big DELIVER TO block (name, address, phone), a small From line, the order
    number, and a prominent COD banner when payment is collected on delivery.
    """
    try:
        from apps.core.models import SiteSettings
        site = SiteSettings.get_settings()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            topMargin=0.7 * inch, bottomMargin=0.7 * inch,
            leftMargin=0.8 * inch, rightMargin=0.8 * inch,
        )
        styles = getSampleStyleSheet()
        from_style = ParagraphStyle("lblFrom", parent=styles["Normal"], fontSize=9.5, textColor=colors.HexColor("#6b6258"))
        to_label = ParagraphStyle("lblTo", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#B8945A"))
        name_style = ParagraphStyle("lblName", parent=styles["Normal"], fontSize=17, leading=21, fontName="Helvetica-Bold", textColor=colors.HexColor("#161310"))
        addr_style = ParagraphStyle("lblAddr", parent=styles["Normal"], fontSize=13, leading=19, textColor=colors.HexColor("#2B2B2B"))
        meta_style = ParagraphStyle("lblMeta", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#8a7f70"))
        cod_style = ParagraphStyle("lblCod", parent=styles["Normal"], fontSize=14, fontName="Helvetica-Bold", textColor=colors.white, alignment=1)

        order_list = list(orders)
        elements = []
        for idx, order in enumerate(order_list):
            from_line = f"<b>From:</b> {site.site_name}"
            if site.contact_phone:
                from_line += f" &nbsp;·&nbsp; {site.contact_phone}"

            addr_parts = [order.shipping_address_line1]
            if order.shipping_address_line2:
                addr_parts.append(order.shipping_address_line2)
            addr_parts.append(f"{order.shipping_city}, {order.shipping_state} - {order.shipping_pincode}")
            addr_parts.append(order.shipping_country)
            addr_html = "<br/>".join(p for p in addr_parts if p)

            rows = [
                [Paragraph(from_line, from_style)],
                [Paragraph("DELIVER TO", to_label)],
                [Paragraph(order.shipping_full_name, name_style)],
                [Paragraph(addr_html, addr_style)],
                [Paragraph(f"<b>Phone:</b> {order.shipping_phone}", addr_style)],
                [Paragraph(f"Order #{order.order_number} &nbsp;·&nbsp; {order.created_at.strftime('%d %b %Y')}", meta_style)],
            ]
            is_cod = order.payment_method == "cod" and order.payment_status != "paid"
            if is_cod:
                rows.append([Paragraph(f"CASH ON DELIVERY — COLLECT Rs.{order.total}", cod_style)])

            label = Table(rows, colWidths=[6.2 * inch])
            style = [
                ("BOX", (0, 0), (-1, -1), 1.4, colors.HexColor("#B8945A")),
                ("LEFTPADDING", (0, 0), (-1, -1), 20),
                ("RIGHTPADDING", (0, 0), (-1, -1), 20),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (0, 0), 18),
                ("BOTTOMPADDING", (0, 1), (0, 1), 8),
            ]
            if is_cod:
                style += [
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#2B2B2B")),
                    ("TOPPADDING", (0, -1), (-1, -1), 11),
                    ("BOTTOMPADDING", (0, -1), (-1, -1), 11),
                    ("LEFTPADDING", (0, -1), (-1, -1), 6),
                    ("RIGHTPADDING", (0, -1), (-1, -1), 6),
                ]
            label.setStyle(TableStyle(style))
            elements.append(label)
            if idx < len(order_list) - 1:
                elements.append(PageBreak())

        doc.build(elements)
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"Error generating shipping labels PDF: {e}")
        return None
