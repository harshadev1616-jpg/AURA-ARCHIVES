# Default settings module.
#
# `aura_archives.settings` resolves to the local *preview* config: DEBUG=False
# with WhiteNoise serving collected static files. DEBUG=True is intentionally
# avoided here because this project nests MEDIA_URL (/static/media/) inside
# STATIC_URL (/static/), which Django's StaticFilesStorage rejects under DEBUG.
#
# Deployments and explicit runs override this by setting DJANGO_SETTINGS_MODULE
# (e.g. aura_archives.settings.production or .development).
from .preview import *  # noqa
