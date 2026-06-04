from django.http import HttpResponse


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /aura-admin/",
        "Disallow: /accounts/",
        "Sitemap: /sitemap.xml",
    ]
    return HttpResponse(chr(10).join(lines), content_type="text/plain")
