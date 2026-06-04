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
            [f"Status: {order.status.upper()}", f"Amount: ₹{order.total_amount:.2f}"],
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
            ['TOTAL:', f"₹{order.total_amount:.2f}"],
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
                [f"Status: {order.status.upper()}", f"Total: ₹{order.total_amount:.2f}"],
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
            
            # Shipping info
            elements.append(Paragraph("SHIPPING ADDRESS", heading_style))
            if hasattr(order, 'shipping_address') and order.shipping_address:
                address = order.shipping_address
                address_text = f"{address.street}, {address.city}, {address.state} {address.zip_code}"
            else:
                address_text = "Address not available"
            elements.append(Paragraph(address_text, styles['Normal']))
            elements.append(Spacer(1, 0.2 * inch))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"Error generating packing slip PDF: {e}")
        return None
