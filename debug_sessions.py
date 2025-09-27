# -*- coding: utf-8 -*-
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mediremind_backend.settings")
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from django.utils import timezone

print("=== Session Configuration Debug ===")
from django.conf import settings
print(f"SESSION_ENGINE: {getattr(settings, 'SESSION_ENGINE', 'default')}")
print(f"SESSION_COOKIE_AGE: {settings.SESSION_COOKIE_AGE}")
print(f"SESSION_SAVE_EVERY_REQUEST: {settings.SESSION_SAVE_EVERY_REQUEST}")
print(f"SESSION_COOKIE_DOMAIN: {settings.SESSION_COOKIE_DOMAIN}")
print(f"SESSION_COOKIE_SAMESITE: {settings.SESSION_COOKIE_SAMESITE}")

print("\n=== Active Sessions ===")
active_sessions = Session.objects.filter(expire_date__gt=timezone.now())
print(f"Total active sessions: {active_sessions.count()}")

for session in active_sessions[:5]:  # Show first 5 sessions
    session_data = session.get_decoded()
    print(f"Session Key: {session.session_key[:10]}...")
    print(f"Expires: {session.expire_date}")
    print(f"Data keys: {list(session_data.keys())}")
    if "oauth_state" in session_data:
        print(f"  oauth_state: {session_data['oauth_state'][:20]}...")
    if "oauth_user_id" in session_data:
        print(f"  oauth_user_id: {session_data['oauth_user_id']}")
    print("---")