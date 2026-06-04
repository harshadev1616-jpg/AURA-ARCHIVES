import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'aura_archives.settings.production'
os.environ['VERCEL'] = '1'

import django
django.setup()

from django.test import Client
client = Client()

# Try different host headers
hosts = ['testserver', 'aura-archives.vercel.app', 'localhost']
for host in hosts:
    try:
        response = client.get('/', HTTP_HOST=host)
        print(f"Host {host}: Status {response.status_code}")
    except Exception as e:
        print(f"Host {host}: Error {type(e).__name__}: {e}")
