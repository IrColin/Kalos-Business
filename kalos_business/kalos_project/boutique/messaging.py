"""Service de messagerie interchangeable.

Par défaut, Kalos Business utilise un backend local : les notifications sont
enregistrées en base et les e-mails sont écrits dans la console du serveur.
Aucune clé API n'est nécessaire. Pour brancher SendGrid, Twilio, WhatsApp ou
un autre fournisseur, créez une classe avec une méthode ``send()`` puis
modifiez ``KALOS_MESSAGING_BACKEND`` dans settings.py.
"""

from django.conf import settings
from django.core.mail import send_mail
from django.utils.module_loading import import_string

from .models import Notification


class BaseMessagingBackend:
    def send(self, subject, message, recipient=None, *, user=None, link=''):
        raise NotImplementedError


class DatabaseMessagingBackend(BaseMessagingBackend):
    """Notification interne + e-mail via le backend configuré (console)."""

    def send(self, subject, message, recipient=None, *, user=None, link=''):
        if user and getattr(user, 'is_authenticated', False):
            Notification.objects.create(user=user, title=subject, body=message, link=link)
        if recipient:
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=[recipient],
                fail_silently=True,
            )


class EmailMessagingBackend(BaseMessagingBackend):
    """E-mail uniquement."""

    def send(self, subject, message, recipient=None, *, user=None, link=''):
        if recipient:
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=[recipient],
                fail_silently=True,
            )


class ConsoleMessagingBackend(BaseMessagingBackend):
    """Affichage seul, utile pour le développement sans base."""

    def send(self, subject, message, recipient=None, *, user=None, link=''):
        print(f'[KALOS MSG] {subject} -> {recipient or (user and user.email)}\n{message}')


def get_backend():
    path = getattr(
        settings,
        'KALOS_MESSAGING_BACKEND',
        'boutique.messaging.DatabaseMessagingBackend',
    )
    return import_string(path)()


def send_message(subject, message, recipient=None, *, user=None, link=''):
    return get_backend().send(subject, message, recipient, user=user, link=link)


def notify_order(order, subject, body):
    """Notifie le client de l'avancement de sa commande."""
    send_message(
        subject,
        body,
        recipient=order.email,
        user=order.user,
        link='/mes-commandes/',
    )
