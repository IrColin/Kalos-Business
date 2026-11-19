"""
Django settings for kalos_project project.

Projet : KALOS BUSINESS — boutique e-commerce (paiements simulés + messagerie).
"""

from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-4p@m72i_6636d+15ss4pmd4uxp9*%4!q0#070^$!)3r=^qhyo9'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'boutique',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'kalos_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'boutique.context_processors.site_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'kalos_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

DEFAULT_FROM_EMAIL = 'Kalos Business <contact@kalosbusiness.test>'

# Messagerie locale : aucune clé API requise. Les e-mails sont affichés dans la
# console du serveur (backend console) et enregistrés dans la base de données.
MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}

# ---------------------------------------------------------------------------
# Configuration métier Kalos Business
# ---------------------------------------------------------------------------
KALOS_SITE_NAME = 'Kalos Business'
KALOS_SITE_TAGLINE = 'La beauté du quotidien, livrée chez vous.'
KALOS_CONTACT_EMAIL = 'contact@kalosbusiness.test'
KALOS_CONTACT_PHONE = '+33 1 23 45 67 89'
KALOS_CURRENCY = '€'
KALOS_DEFAULT_COUNTRY = 'France'
KALOS_SHIPPING_FEE = Decimal('5.90')
KALOS_FREE_SHIPPING_THRESHOLD = Decimal('100.00')

# PAIEMENT : mode bac à sable par défaut. Les boutons sont réellement
# fonctionnels (validation, transaction, stock, confirmation) mais aucun
# appel réseau ni débit n'est effectué. Voir boutique/payments.py pour brancher
# Stripe / PayPal / CMI plus tard sans toucher au reste du code.
KALOS_PAYMENT_MODE = 'sandbox'
KALOS_DEMO_PAYMENTS = True

# MESSAGERIE : backend interchangeable (base de données + console pour l'instant).
KALOS_MESSAGING_BACKEND = 'boutique.messaging.DatabaseMessagingBackend'
