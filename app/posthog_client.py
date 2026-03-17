"""
PostHog client for server-side event tracking.
Only initializes if POSTHOG_API_KEY is set. Safe to call capture() when disabled.
"""
import os
from dotenv import load_dotenv
load_dotenv()

_posthog = None

def _get_client():
    global _posthog
    if _posthog is None:
        api_key = os.environ.get('POSTHOG_API_KEY')
        host = os.environ.get('POSTHOG_HOST', 'https://us.i.posthog.com')
        if api_key:
            from posthog import Posthog
            _posthog = Posthog(api_key=api_key, host=host)
    return _posthog

def capture(distinct_id, event, properties=None, groups=None):
    """Send an event to PostHog. No-op if PostHog is not configured."""
    client = _get_client()
    if client:
        client.capture(distinct_id=distinct_id, event=event, properties=properties or {}, groups=groups)

def shutdown():
    """Flush and shutdown the PostHog client. Call on app teardown."""
    client = _get_client()
    if client:
        client.shutdown()
