import os
import pytest


@pytest.fixture(autouse=True, scope="session")
def configure_test_env():
    os.environ.setdefault("DB_ENGINE", "django.db.backends.sqlite3")
    os.environ.setdefault("DB_NAME", "db_api.sqlite3")
    os.environ.setdefault("DJANGO_DEBUG", "True")
    os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "testserver,localhost,127.0.0.1")
    os.environ.setdefault("DJANGO_SECURE_SSL_REDIRECT", "False")


@pytest.fixture(autouse=True)
def disable_whitenoise(settings):
    # Remove WhiteNoise for test client to avoid missing package errors locally
    settings.MIDDLEWARE = [
        m for m in settings.MIDDLEWARE if m != 'whitenoise.middleware.WhiteNoiseMiddleware'
    ]


