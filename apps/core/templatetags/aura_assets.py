"""Cache-busting static asset helper.

Appends the file's modification time as a query string so the browser always
fetches a freshly rebuilt asset (e.g. compiled tailwind.css) without a manual
hard-refresh. In production, ManifestStaticFilesStorage already hashes
filenames, so the extra query param is harmless.
"""
import os

from django import template
from django.contrib.staticfiles import finders
from django.http import QueryDict
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


@register.simple_tag(takes_context=True)
def query_replace(context, **kwargs):
    """Return the current query string with the given keys replaced/removed.

    Lets pagination and sort links preserve every other active filter instead
    of dropping them. Pass a falsy value to drop a key (e.g. to clear a filter).
    Always resets `page` to 1 unless `page` is explicitly provided.
    """
    request = context.get("request")
    params = request.GET.copy() if request else QueryDict(mutable=True)
    for key, value in kwargs.items():
        if value in (None, "", False):
            params.pop(key, None)
        else:
            params[key] = value
    if "page" not in kwargs:
        params.pop("page", None)
    return params.urlencode()
