"""Passerelles de paiement.

IMPORTANT — MODE DÉMONSTRATION :
Les trois moyens de paiement ci-dessous sont entièrement fonctionnels dans
l'application (validation des données, création d'une transaction, mise à jour
du stock et de la commande, page de confirmation) mais ne contactent aucun
service externe et ne débitent aucun compte.

Pour passer en production :
  1. Obtenez vos identifiants auprès de votre prestataire (Stripe, PayPal, CMI...).
  2. Créez une classe héritant de ``BaseGateway`` dans ce fichier, ou bien
     installez le SDK du prestataire et appelez-le dans ``charge()``.
  3. Ajoutez la classe à ``GATEWAYS`` et changez ``KALOS_PAYMENT_MODE`` dans
     settings.py. Le reste du site (vues, modèles, templates) reste inchangé.

Aucun numéro de carte complet n'est stocké : seuls le réseau et les 4 derniers
chiffres sont conservés dans la table Transaction.
"""

import secrets
from datetime import datetime

from django.utils import timezone


class PaymentError(Exception):
    """Erreur de paiement affichée à l'utilisateur."""


def luhn_valid(number):
    """Valide un numéro de carte avec l'algorithme de Luhn."""
    digits = [int(char) for char in number if char.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    for index, digit in enumerate(reversed(digits)):
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def detect_brand(number):
    digits = ''.join(char for char in number if char.isdigit())
    if digits.startswith('4'):
        return 'Visa'
    if digits.startswith(('34', '37')):
        return 'American Express'
    if len(digits) >= 4 and digits[:2].isdigit() and 51 <= int(digits[:2]) <= 55:
        return 'Mastercard'
    if len(digits) >= 4 and digits[:4].isdigit() and 2221 <= int(digits[:4]) <= 2720:
        return 'Mastercard'
    if digits.startswith(('62', '81')):
        return 'UnionPay'
    return 'Carte'


def parse_expiry(value):
    raw = value.replace(' ', '').replace('/', '')
    if len(raw) != 4 or not raw.isdigit():
        raise PaymentError('Format d’expiration invalide (utilisez MM/AA).')
    month, year = int(raw[:2]), 2000 + int(raw[2:])
    if not 1 <= month <= 12:
        raise PaymentError('Mois d’expiration invalide.')
    expiry = datetime(year, month, 1).date()
    if expiry < timezone.localdate().replace(day=1):
        raise PaymentError('Cette carte est expirée.')
    return expiry


class BaseGateway:
    code = 'base'
    label = 'Paiement'
    demo = True

    def charge(self, order, **data):
        raise NotImplementedError


class SandboxCardGateway(BaseGateway):
    """Paiement par carte simulé : accepte toute carte valide selon Luhn.

    Carte de test : 4242 4242 4242 4242 — 12/30 — CVC 123.
    """

    code = 'card'
    label = 'Carte bancaire'
    demo = True

    def charge(self, order, **data):
        number = ''.join(ch for ch in data.get('card_number', '') if ch.isdigit())
        holder = (data.get('cardholder') or '').strip()
        if len(holder) < 3:
            raise PaymentError('Indiquez le nom du titulaire de la carte.')
        if not luhn_valid(number):
            raise PaymentError('Numéro de carte invalide.')
        parse_expiry(data.get('expiry', ''))
        cvc = ''.join(ch for ch in data.get('cvc', '') if ch.isdigit())
        if not 3 <= len(cvc) <= 4:
            raise PaymentError('Cryptogramme (CVC) invalide.')

        return {
            'status': 'succeeded',
            'provider': self.code,
            'reference': 'CRD-' + secrets.token_hex(5).upper(),
            'amount': order.total,
            'card_brand': detect_brand(number),
            'card_last4': number[-4:],
            'message': 'Paiement accepté.',
        }


class SandboxPayPalGateway(BaseGateway):
    """Paiement PayPal simulé : l'utilisateur confirme explicitement."""

    code = 'paypal'
    label = 'PayPal'
    demo = True

    def charge(self, order, **data):
        email = (data.get('email') or '').strip()
        if '@' not in email or '.' not in email.split('@')[-1]:
            raise PaymentError('Saisissez une adresse e-mail PayPal valide.')
        if not data.get('confirm'):
            raise PaymentError('Veuillez confirmer le paiement PayPal.')

        return {
            'status': 'succeeded',
            'provider': self.code,
            'reference': 'PPL-' + secrets.token_hex(5).upper(),
            'amount': order.total,
            'card_brand': '',
            'card_last4': '',
            'message': 'Paiement PayPal accepté.',
        }


class CashOnDeliveryGateway(BaseGateway):
    """Commande confirmée, règlement à la livraison."""

    code = 'cod'
    label = 'Paiement à la livraison'
    demo = False

    def charge(self, order, **data):
        return {
            'status': 'cod_confirmed',
            'provider': self.code,
            'reference': 'COD-' + secrets.token_hex(5).upper(),
            'amount': order.total,
            'card_brand': '',
            'card_last4': '',
            'message': 'Commande confirmée. Le paiement s’effectuera à la livraison.',
        }


GATEWAYS = {
    gateway.code: gateway()
    for gateway in (SandboxCardGateway, SandboxPayPalGateway, CashOnDeliveryGateway)
}

PAYMENT_METHODS = [
    {
        'code': 'card',
        'label': 'Carte bancaire',
        'hint': 'Visa, Mastercard, Amex — paiement sécurisé',
        'icon': 'bi-credit-card-2-front',
        'demo': True,
    },
    {
        'code': 'paypal',
        'label': 'PayPal',
        'hint': 'Confirmez avec votre adresse PayPal',
        'icon': 'bi-paypal',
        'demo': True,
    },
    {
        'code': 'cod',
        'label': 'Paiement à la livraison',
        'hint': 'Réglez en espèces ou par carte au livreur',
        'icon': 'bi-truck',
        'demo': False,
    },
]


def get_gateway(code):
    try:
        return GATEWAYS[code]
    except KeyError:
        raise PaymentError('Moyen de paiement inconnu.')
