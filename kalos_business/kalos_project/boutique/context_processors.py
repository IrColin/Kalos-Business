"""Variables partagées avec tous les templates."""

from .app_settings import get_all
from .cart import get_cart
from .models import Category


def site_context(request):
    values = get_all()
    cart = None
    try:
        cart = get_cart(request)
    except Exception:
        # Ne jamais faire échouer une page à cause du panier.
        pass

    notifications = []
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        notifications = list(user.notifications.filter(is_read=False)[:5])

    return {
        'kalos_name': values['site_name'],
        'kalos_tagline': values['site_tagline'],
        'kalos_currency': values['currency'],
        'kalos_contact_email': values['contact_email'],
        'kalos_contact_phone': values['contact_phone'],
        'kalos_shop_open': values['shop_open'],
        'cart': cart,
        'nav_categories': Category.objects.filter(is_active=True)[:8],
        'notifications': notifications,
    }
