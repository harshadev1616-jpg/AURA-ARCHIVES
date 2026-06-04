from django.shortcuts import render, get_object_or_404
from .models import Page


def page_detail(request, slug):
    page = get_object_or_404(Page, slug=slug, is_active=True)
    return render(request, "cms/page.html", {"page": page})
