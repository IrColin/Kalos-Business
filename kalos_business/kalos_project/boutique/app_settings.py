"""Paramètres de l'application modifiables depuis le tableau de bord.

Les valeurs sont stockées en base (modèle ``Setting``) et surchargent les
valeurs par défaut définies dans settings.py. Un cache mémoire évite une
requête par affichage ; il est invalidé à chaque enregistrement.
"""

from collections import OrderedDict
from decimal import Decimal

from django.conf import settings as django_settings
from django.core.cache import cache

from .models import Setting

CACHE_KEY = 'kalos_app_settings_v1'

DEFINITIONS = OrderedDict([
    ('site_name', {
        'label': 'Nom du site', 'group': 'Général', 'type': 'text',
        'default': getattr(django_settings, 'KALOS_SITE_NAME', 'Kalos Business'),
    }),
    ('site_tagline', {
        'label': 'Slogan', 'group': 'Général', 'type': 'text',
        'default': getattr(django_settings, 'KALOS_SITE_TAGLINE', ''),
    }),
    ('currency', {
        'label': 'Devise', 'group': 'Général', 'type': 'text',
        'default': getattr(django_settings, 'KALOS_CURRENCY', '€'),
    }),
    ('contact_email', {
        'label': 'E-mail de contact', 'group': 'Général', 'type': 'text',
        'default': getattr(django_settings, 'KALOS_CONTACT_EMAIL', 'contact@kalosbusiness.test'),
    }),
    ('contact_phone', {
        'label': 'Téléphone', 'group': 'Général', 'type': 'text',
        'default': getattr(django_settings, 'KALOS_CONTACT_PHONE', '+33 1 23 45 67 89'),
    }),
    ('default_country', {
        'label': 'Pays par défaut', 'group': 'Général', 'type': 'text',
        'default': getattr(django_settings, 'KALOS_DEFAULT_COUNTRY', 'France'),
    }),
    ('shop_open', {
        'label': 'Boutique ouverte (commande autorisée)', 'group': 'Boutique', 'type': 'bool',
        'default': True,
        'help': 'Si désactivé, les visiteurs ne peuvent plus passer commande.',
    }),
    ('shipping_fee', {
        'label': 'Frais de livraison', 'group': 'Boutique', 'type': 'number',
        'default': getattr(django_settings, 'KALOS_SHIPPING_FEE', Decimal('5.90')),
        'help': 'Montant facturé lorsque le seuil de livraison offerte n’est pas atteint.',
    }),
    ('free_shipping_threshold', {
        'label': 'Seuil de livraison offerte', 'group': 'Boutique', 'type': 'number',
        'default': getattr(django_settings, 'KALOS_FREE_SHIPPING_THRESHOLD', Decimal('100.00')),
    }),
    ('global_discount', {
        'label': 'Réduction globale (%)', 'group': 'Promotions', 'type': 'number',
        'default': Decimal('0'),
        'help': 'Appliquée à toutes les commandes, cumulable avec le code promo.',
    }),
    ('promo_code', {
        'label': 'Code promo actif', 'group': 'Promotions', 'type': 'text',
        'default': 'KALOS10',
    }),
    ('promo_discount', {
        'label': 'Réduction du code promo (%)', 'group': 'Promotions', 'type': 'number',
        'default': Decimal('10'),
    }),
])


def _convert(definition, value):
    kind = definition['type']
    if value in (None, ''):
        return definition['default']
    if kind == 'number':
        try:
            return Decimal(str(value))
        except Exception:
            return definition['default']
    if kind == 'bool':
        return str(value).lower() not in ('0', 'false', 'no', 'off', '')
    return str(value)


def get_all():
    """Retourne tous les paramètres avec leur type Python."""
    values = cache.get(CACHE_KEY)
    if values is None:
        stored = {row.key: row.value for row in Setting.objects.all()}
        values = {
            key: _convert(definition, stored.get(key))
            for key, definition in DEFINITIONS.items()
        }
        cache.set(CACHE_KEY, values, 300)
    return values


def get_value(key, fallback=None):
    values = get_all()
    return values.get(key, fallback)


def save_values(cleaned_data):
    """Enregistre les valeurs issues du formulaire et invalide le cache."""
    for key, value in cleaned_data.items():
        if key not in DEFINITIONS:
            continue
        if isinstance(value, bool):
            stored = '1' if value else '0'
        elif value is None:
            stored = ''
        else:
            stored = str(value)
        Setting.objects.update_or_create(key=key, defaults={'value': stored})
    cache.delete(CACHE_KEY)
    return get_all()
