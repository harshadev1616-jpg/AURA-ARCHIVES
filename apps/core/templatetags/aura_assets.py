"""Cache-busting static asset helper.

Appends the file's modification time as a query string so the browser always
fetches a freshly rebuilt asset (e.g. compiled tailwind.css) without a manual
hard-refresh. In production, ManifestStaticFilesStorage already hashes
filenames, so the extra query param is harmless.
"""
import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def static_v(path):
    url = static(path)
    try:
        abs_path = finders.find(path)
        if abs_path and os.path.exists(abs_path):
            mtime = int(os.path.getmtime(abs_path))
            sep = "&" if "?" in url else "?"
            return f"{url}{sep}v={mtime}"
    except Exception:
        pass
    return url
