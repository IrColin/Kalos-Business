"""Vues de la boutique Kalos Business."""

from collections import OrderedDict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render, resolve_url
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .app_settings import DEFINITIONS, get_all, get_value, save_values
from .cart import CartError, add_item, cart_totals, clear_cart, get_cart, remove_item, set_quantity
from .forms import CardPaymentForm, CheckoutForm, ContactForm, PayPalPaymentForm, PromoForm, SettingsForm
from .messaging import notify_order, send_message
from .models import Category, Message, Order, OrderItem, Product, Transaction
from .payments import PaymentError, PAYMENT_METHODS, get_gateway


def _safe_next(request):
    """Redirection POST sûre : uniquement une URL locale."""
    target = request.POST.get('next', '')
    if target and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(target)
    return redirect('cart')


def _can_access_order(request, order):
    if order.user_id and request.user.is_authenticated and order.user_id == request.user.id:
        return True
    return request.session.get('kalos_current_order') == order.reference


def _group_settings():
    """Regroupe les paramètres par catégorie pour l'affichage."""
    groups = OrderedDict()
    for key, definition in DEFINITIONS.items():
        groups.setdefault(definition['group'], []).append((key, definition))
    return groups


def _setting_sections(form):
    """Prépare les champs groupés pour le template, sans filtre personnalisé."""
    sections = []
    for group, items in _group_settings().items():
        fields = []
        for key, definition in items:
            field = form[key]
            fields.append({
                'label': definition['label'],
                'type': definition['type'],
                'help': definition.get('help', ''),
                'field': field,
                'errors': field.errors,
            })
        sections.append({'name': group, 'fields': fields})
    return sections


class KalosLoginView(LoginView):
    """Connexion : les membres de l'équipe arrivent sur leur tableau de bord."""

    template_name = 'boutique/auth/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        target = self.get_redirect_url()
        if target:
            return target
        if self.request.user.is_staff:
            return reverse('dashboard')
        return resolve_url(settings.LOGIN_REDIRECT_URL)


@user_passes_test(lambda user: user.is_staff, login_url='login')
def admin_dashboard(request):
    """Tableau de bord réservé à l'équipe (is_staff), avec réglages de l'app."""
    if request.method == 'POST':
        form = SettingsForm(request.POST)
        if form.is_valid():
            save_values(form.cleaned_data)
            messages.success(request, 'Paramètres enregistrés avec succès.')
            return redirect(reverse('dashboard') + '#parametres')
    else:
        form = SettingsForm()

    orders = Order.objects.all()
    paid_orders = orders.filter(status__in=['paid', 'processing', 'shipped', 'delivered'])
    revenue = paid_orders.aggregate(total=Sum('total'))['total'] or 0

    return render(
        request,
        'boutique/dashboard.html',
        {
            'orders_count': orders.count(),
            'pending_count': orders.filter(status='pending').count(),
            'revenue': revenue,
            'products_count': Product.objects.count(),
            'low_stock': Product.objects.filter(is_active=True, stock__lte=5).order_by('stock')[:6],
            'unread_messages': Message.objects.filter(status='open').count(),
            'recent_orders': orders.select_related('user')[:8],
            'recent_messages': Message.objects.all()[:5],
            'settings_form': form,
            'setting_definitions': DEFINITIONS,
            'settings_values': get_all(),
            'setting_sections': _setting_sections(form),
        },
    )


def home(request):
    featured = Product.objects.filter(is_active=True, is_featured=True).select_related('category')[:8]
    latest = Product.objects.filter(is_active=True).exclude(is_featured=True).select_related('category')[:4]
    categories = Category.objects.filter(is_active=True)
    return render(
        request,
        'boutique/home.html',
        {'featured': featured, 'latest': latest, 'categories': categories},
    )


def catalog(request):
    products = Product.objects.filter(is_active=True).select_related('category')
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('categorie', '')
    sort = request.GET.get('tri', '-created_at')

    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(short_description__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        )
    if category_slug:
        products = products.filter(category__slug=category_slug)

    order_map = {
        'nom': 'name',
        'prix_asc': 'price',
        'prix_desc': '-price',
        'recent': '-created_at',
    }
    products = products.order_by(order_map.get(sort, '-created_at'))

    paginator = Paginator(products, 9)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(
        request,
        'boutique/catalog.html',
        {
            'page_obj': page_obj,
            'categories': Category.objects.filter(is_active=True),
            'query': query,
            'category_slug': category_slug,
            'sort': sort,
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = Product.objects.filter(
        is_active=True, category=product.category
    ).exclude(pk=product.pk).select_related('category')[:4]
    return render(
        request,
        'boutique/product_detail.html',
        {'product': product, 'related': related},
    )


def cart_view(request):
    cart = get_cart(request)
    promo_code = request.session.get('kalos_promo')
    items = cart.items.select_related('product')
    return render(
        request,
        'boutique/cart.html',
        {
            'items': items,
            'totals': cart_totals(cart, promo_code),
            'promo_form': PromoForm(initial={'code': promo_code or ''}),
        },
    )


def cart_promo(request):
    """Applique ou retire le code promo configuré dans les paramètres."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    if request.POST.get('remove'):
        request.session.pop('kalos_promo', None)
        messages.success(request, 'Code promo retiré.')
    else:
        form = PromoForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code'].strip()
            values = get_all()
            expected = str(values['promo_code'] or '').strip().upper()
            if expected and code.upper() == expected:
                request.session['kalos_promo'] = code
                messages.success(request, f"Code promo appliqué : -{values['promo_discount']} %.")
            else:
                messages.error(request, 'Ce code promo n’est pas valide.')
    return redirect('cart')


def cart_add(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    product = get_object_or_404(Product, pk=request.POST.get('product_id'), is_active=True)
    try:
        quantity = int(request.POST.get('quantity', 1))
        _, limited = add_item(get_cart(request), product, quantity)
        if limited:
            messages.warning(request, f'Stock limité : quantité ajustée à {product.stock} pour « {product.name} ».')
        else:
            messages.success(request, f'« {product.name} » ajouté au panier.')
    except (CartError, ValueError) as exc:
        messages.error(request, str(exc))
    return _safe_next(request)


def cart_update(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    cart = get_cart(request)
    for key, value in request.POST.items():
        if key.startswith('qty_'):
            try:
                set_quantity(cart, int(key[4:]), int(value))
            except (CartError, ValueError):
                continue
    messages.success(request, 'Panier mis à jour.')
    return redirect('cart')


def cart_remove(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        remove_item(get_cart(request), int(request.POST.get('item_id', 0)))
        messages.success(request, 'Article retiré du panier.')
    except (CartError, ValueError) as exc:
        messages.error(request, str(exc))
    return redirect('cart')


def checkout(request):
    cart = get_cart(request)
    items = list(cart.items.select_related('product'))
    if not items:
        messages.warning(request, 'Votre panier est vide.')
        return redirect('cart')
    if not get_value('shop_open', True):
        messages.warning(request, 'La boutique est temporairement fermée aux commandes.')
        return redirect('catalog')

    totals = cart_totals(cart, request.session.get('kalos_promo'))
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                full_name=data['full_name'],
                email=data['email'],
                phone=data['phone'],
                address=data['address'],
                city=data['city'],
                postal_code=data['postal_code'],
                country=data['country'],
                notes=data['notes'],
                subtotal=totals['subtotal'],
                discount=totals['discount'],
                shipping=totals['shipping'],
                total=totals['total'],
                status='pending',
            )
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    name=item.product.name,
                    unit_price=item.product.price,
                    quantity=item.quantity,
                )
            request.session['kalos_current_order'] = order.reference
            messages.success(request, 'Commande enregistrée. Choisissez votre moyen de paiement.')
            return redirect('payment', reference=order.reference)
    else:
        user = request.user
        form = CheckoutForm(
            initial={
                'full_name': (user.get_full_name() or user.username) if user.is_authenticated else '',
                'email': user.email if user.is_authenticated else '',
            }
        )
    return render(
        request,
        'boutique/checkout.html',
        {'form': form, 'items': items, 'totals': totals},
    )


def payment(request, reference):
    order = get_object_or_404(Order, reference=reference)
    if not _can_access_order(request, order):
        raise Http404('Commande introuvable.')

    if order.status != 'pending':
        return redirect('payment_success', reference=order.reference)

    method = request.POST.get('method') or request.GET.get('method') or 'card'
    if method not in {m['code'] for m in PAYMENT_METHODS}:
        method = 'card'

    card_form = CardPaymentForm(request.POST if request.method == 'POST' and method == 'card' else None)
    paypal_form = PayPalPaymentForm(request.POST if request.method == 'POST' and method == 'paypal' else None)

    if request.method == 'POST':
        active_form = {'card': card_form, 'paypal': paypal_form}.get(method)
        if active_form and active_form.is_valid():
            gateway = get_gateway(method)
            data = dict(active_form.cleaned_data)
            if method == 'paypal':
                data['confirm'] = True
            try:
                result = gateway.charge(order, **data)

                with transaction.atomic():
                    current = Order.objects.select_for_update().get(pk=order.pk)
                    if current.status != 'pending':
                        raise PaymentError('Cette commande a déjà été traitée.')

                    for line in current.items.select_related('product'):
                        if not line.product_id:
                            continue
                        product = Product.objects.select_for_update().get(pk=line.product_id)
                        if product.stock < line.quantity:
                            raise PaymentError(f"Stock insuffisant pour « {product.name} ».")
                        product.stock -= line.quantity
                        product.save(update_fields=['stock'])

                    paid = result['status'] == 'succeeded'
                    current.status = 'paid' if paid else 'cod_confirmed'
                    current.payment_method = method
                    current.transaction_ref = result['reference']
                    current.paid_at = timezone.now() if paid else None
                    current.save()

                    Transaction.objects.create(
                        order=current,
                        provider=result['provider'],
                        reference=result['reference'],
                        amount=result['amount'],
                        status=result['status'],
                        card_brand=result['card_brand'],
                        card_last4=result['card_last4'],
                        response={
                            'mode': getattr(settings, 'KALOS_PAYMENT_MODE', 'sandbox'),
                            'message': result['message'],
                        },
                    )
                    clear_cart(get_cart(request))
                    request.session.pop('kalos_promo', None)

                notify_order(
                    current,
                    f'Kalos Business — commande {current.reference} confirmée',
                    (
                        f'Bonjour {current.full_name},\n\nVotre commande {current.reference} '
                        f'est confirmée pour un montant de {current.total} {settings.KALOS_CURRENCY}. '
                        f'Moyen de paiement : {current.get_payment_method_display()}.\n\n'
                        'Merci pour votre confiance,\nL’équipe Kalos Business'
                    ),
                )
                messages.success(request, result['message'])
                return redirect('payment_success', reference=order.reference)

            except PaymentError as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, 'Vérifiez les informations de paiement.')

    return render(
        request,
        'boutique/payment.html',
        {
            'order': order,
            'items': order.items.select_related('product'),
            'methods': PAYMENT_METHODS,
            'method': method,
            'card_form': card_form,
            'paypal_form': paypal_form,
        },
    )


def payment_success(request, reference):
    order = get_object_or_404(Order, reference=reference)
    if not _can_access_order(request, order):
        raise Http404('Commande introuvable.')
    return render(
        request,
        'boutique/payment_success.html',
        {'order': order, 'transaction': getattr(order, 'transaction', None)},
    )


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    return render(request, 'boutique/my_orders.html', {'orders': orders})


def order_detail(request, reference):
    order = get_object_or_404(Order, reference=reference)
    if not _can_access_order(request, order):
        raise Http404('Commande introuvable.')
    return render(
        request,
        'boutique/order_detail.html',
        {'order': order, 'transaction': getattr(order, 'transaction', None)},
    )


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            message = Message.objects.create(
                user=request.user if request.user.is_authenticated else None,
                name=data['name'],
                email=data['email'],
                subject=data['subject'],
                body=data['body'],
            )
            send_message(
                f'[Kalos Business] Nouveau message : {message.subject}',
                f'De : {message.name} <{message.email}>\n\n{message.body}\n\n'
                f'Répondre : {request.build_absolute_uri(message.get_thread_url())}',
                get_value('contact_email', 'contact@kalosbusiness.test'),
            )
            send_message(
                'Kalos Business — nous avons reçu votre message',
                f'Bonjour {message.name},\n\nVotre message « {message.subject} » a bien été reçu. '
                'Notre équipe vous répondra rapidement.\n\n'
                f'Suivre la conversation : {request.build_absolute_uri(message.get_thread_url())}\n\n'
                'L’équipe Kalos Business',
                message.email,
            )
            messages.success(request, 'Votre message a été envoyé. Suivez la réponse ici.')
            return redirect('message_thread', token=message.thread_token)
    else:
        user = request.user
        form = ContactForm(
            initial={
                'name': (user.get_full_name() or user.username) if user.is_authenticated else '',
                'email': user.email if user.is_authenticated else '',
            }
        )
    return render(request, 'boutique/contact.html', {'form': form})


def message_thread(request, token):
    thread = get_object_or_404(Message, thread_token=token)
    if request.method == 'POST':
        followup = Message.objects.create(
            user=request.user if request.user.is_authenticated else None,
            name=thread.name,
            email=thread.email,
            subject=f'Re : {thread.subject.lstrip("Re : ")}',
            body=request.POST.get('body', '').strip() or '(suite de la conversation)',
        )
        send_message(
            f'[Kalos Business] Suite : {followup.subject}',
            f'De : {followup.name} <{followup.email}>\n\n{followup.body}',
            get_value('contact_email', 'contact@kalosbusiness.test'),
        )
        messages.success(request, 'Votre réponse a été transmise.')
        return redirect('message_thread', token=followup.thread_token)
    return render(request, 'boutique/message_thread.html', {'thread': thread})


def about(request):
    return render(request, 'boutique/about.html')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Bienvenue chez Kalos Business !')
            return redirect('home')
    else:
        form = UserCreationForm()
    for field in form.fields.values():
        field.widget.attrs['class'] = 'form-control'
    return render(request, 'boutique/auth/register.html', {'form': form})
