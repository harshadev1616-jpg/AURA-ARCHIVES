from .models import Announcement, Banner, Page


def cms_content(request):
    try:
        announcements = Announcement.objects.filter(is_active=True)
        footer_pages = Page.objects.filter(is_active=True, show_in_footer=True).order_by('sort_order')
        header_pages = Page.objects.filter(is_active=True, show_in_header=True).order_by('sort_order')
        return {
            'announcements': announcements,
            'footer_pages': footer_pages,
            'header_pages': header_pages,
        }
    except Exception:
        return {'announcements': [], 'footer_pages': [], 'header_pages': []}
