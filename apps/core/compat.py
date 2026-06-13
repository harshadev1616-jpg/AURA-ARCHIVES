"""Runtime compatibility shims.

Django 5.0 predates Python 3.14, and a couple of its internal idioms break on
the newer interpreter. These patches are intentionally equivalent to the
original behaviour, so they're safe to apply on every Python version.
"""


def patch_template_context_copy():
    """Fix admin changelists 500-ing on Python 3.14.

    Django 5.0's ``BaseContext.__copy__`` does ``duplicate = copy(super())``.
    On Python 3.14 ``copy()`` of a zero-arg ``super`` proxy no longer returns a
    copy of the underlying instance — it returns a bare ``super`` object with no
    ``dicts`` attribute — so every template that copies its context (e.g. the
    admin ``{% result_list %}`` inclusion tag) raises ``AttributeError`` and the
    whole changelist returns 500.

    Replace ``__copy__`` with an explicit shallow copy that is behaviourally
    identical to the original on all supported Python versions.
    """
    from django.template.context import BaseContext

    def __copy__(self):
        duplicate = self.__class__.__new__(self.__class__)
        duplicate.__dict__.update(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate

    BaseContext.__copy__ = __copy__
