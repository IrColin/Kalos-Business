"""Gestion du panier (session pour les visiteurs, compte pour les utilisateurs)."""

from decimal import Decimal

from .app_settings import get_all
from .models import Cart, CartItem


class CartError(Exception):
    """Erreur métier liée au panier (stock, quantité...)."""


def get_cart(request):
    """Retourne le panier de l'utilisateur connecté ou celui de la session."""
    user = request.user if request.user.is_authenticated else None

    if user:
        cart, _ = Cart.objects.get_or_create(user=user)
        # Fusionne un éventuel panier anonyme au moment de la connexion.
        session_key = request.session.session_key
        if session_key:
            anonymous = Cart.objects.filter(session_key=session_key).exclude(pk=cart.pk).first()
            if anonymous:
                for item in anonymous.items.select_related('product'):
                    try:
                        add_item(cart, item.product, item.quantity)
                    except CartError:
                        pass
                anonymous.delete()
        return cart

    if not request.session.session_key:
        request.session.create()
    cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart


def add_item(cart, product, quantity=1):
    """Ajoute une quantité au panier. Retourne (ligne, stock_limité)."""
    if quantity <= 0:
        raise CartError('La quantité doit être positive.')
    if not product.is_active:
        raise CartError('Ce produit n’est plus disponible.')
    if product.stock <= 0:
        raise CartError('Ce produit est en rupture de stock.')

    item, _ = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': 0})
    wanted = item.quantity + quantity
    limited = wanted > product.stock
    item.quantity = product.stock if limited else wanted
    item.save(update_fields=['quantity'])
    cart.save(update_fields=['updated_at'])
    return item, limited


def set_quantity(cart, item_id, quantity):
    """Définit la quantité d'une ligne, en respectant le stock."""
    item = CartItem.objects.filter(pk=item_id, cart=cart).select_related('product').first()
    if not item:
        raise CartError('Ligne de panier introuvable.')
    if quantity <= 0:
        item.delete()
        return None
    if quantity > item.product.stock:
        quantity = item.product.stock
    item.quantity = quantity
    item.save(update_fields=['quantity'])
    return item


def remove_item(cart, item_id):
    deleted, _ = CartItem.objects.filter(pk=item_id, cart=cart).delete()
    if not deleted:
        raise CartError('Ligne de panier introuvable.')


def clear_cart(cart):
    cart.items.all().delete()


def cart_totals(cart, promo_code=None):
    """Calcule sous-total, réductions, livraison et total.

    Les montants et pourcentages proviennent des paramètres modifiables
    depuis le tableau de bord (voir app_settings.py).
    """
    values = get_all()
    subtotal = cart.subtotal

    percent = values['global_discount']
    promo_applied = bool(
        promo_code
        and values['promo_code']
        and str(promo_code).strip().upper() == str(values['promo_code']).strip().upper()
    )
    if promo_applied:
        percent += values['promo_discount']
    percent = min(max(percent, Decimal('0')), Decimal('100'))

    discount = (subtotal * percent / Decimal('100')).quantize(Decimal('0.01'))
    after_discount = subtotal - discount
    threshold = values['free_shipping_threshold']
    shipping = Decimal('0.00') if after_discount >= threshold else values['shipping_fee']

    return {
        'count': cart.count,
        'subtotal': subtotal,
        'discount': discount,
        'discount_percent': percent,
        'after_discount': after_discount,
        'shipping': shipping,
        'total': after_discount + shipping,
        'free_shipping_left': max(Decimal('0.00'), threshold - after_discount),
        'promo_applied': promo_applied,
    }
