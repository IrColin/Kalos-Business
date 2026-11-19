"""Tests du parcours e-commerce Kalos Business."""

from decimal import Decimal

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from .app_settings import get_value, save_values
from .cart import add_item, cart_totals, get_cart
from .models import Cart, CartItem, Category, Order, Product, Transaction
from .payments import detect_brand, luhn_valid


class PaymentLogicTests(TestCase):
    def test_luhn_and_brand(self):
        self.assertTrue(luhn_valid('4242 4242 4242 4242'))
        self.assertFalse(luhn_valid('4242 4242 4242 4241'))
        self.assertEqual(detect_brand('4242424242424242'), 'Visa')
        self.assertEqual(detect_brand('5555555555554444'), 'Mastercard')

    def test_add_item_respects_stock(self):
        category = Category.objects.create(name='Test')
        product = Product.objects.create(
            category=category, name='Produit test', price=Decimal('10.00'), stock=2
        )
        cart = Cart.objects.create(session_key='test-session')
        item, limited = add_item(cart, product, 3)
        self.assertTrue(limited)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(cart_totals(cart)['subtotal'], Decimal('20.00'))


class CheckoutFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.category = Category.objects.create(name='Mode test')
        self.product = Product.objects.create(
            category=self.category,
            name='Robe test',
            price=Decimal('50.00'),
            stock=5,
            is_active=True,
        )

    def _build_order(self):
        self.client.post(
            reverse('cart_add'),
            {'product_id': self.product.pk, 'quantity': 2, 'next': '/panier/'},
        )
        response = self.client.post(
            reverse('checkout'),
            {
                'full_name': 'Jean Dupont',
                'email': 'jean@example.com',
                'phone': '0600000000',
                'address': '12 rue de la Paix',
                'city': 'Paris',
                'postal_code': '75002',
                'country': 'France',
                'notes': '',
            },
        )
        order = Order.objects.get(reference=self.client.session['kalos_current_order'])
        self.assertEqual(response.status_code, 302)
        # 2 × 50 € = 100 € : le seuil de livraison offerte est atteint.
        self.assertEqual(order.shipping, Decimal('0.00'))
        self.assertEqual(order.total, Decimal('100.00'))
        return order

    def test_full_sandbox_card_payment(self):
        order = self._build_order()
        response = self.client.post(
            reverse('payment', args=[order.reference]),
            {
                'method': 'card',
                'cardholder': 'Jean Dupont',
                'card_number': '4242 4242 4242 4242',
                'expiry': '12/30',
                'cvc': '123',
            },
        )
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, 'paid')
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(Transaction.objects.first().card_last4, '4242')
        self.assertEqual(Cart.objects.get(session_key=self.client.session.session_key).count, 0)
        self.assertRedirects(response, reverse('payment_success', args=[order.reference]))

    def test_invalid_card_keeps_order_pending(self):
        order = self._build_order()
        self.client.post(
            reverse('payment', args=[order.reference]),
            {
                'method': 'card',
                'cardholder': 'Jean Dupont',
                'card_number': '1234 5678 9012 3456',
                'expiry': '12/30',
                'cvc': '123',
            },
        )
        order.refresh_from_db()
        self.assertEqual(order.status, 'pending')
        self.assertEqual(Transaction.objects.count(), 0)
        self.assertEqual(self.product.stock, 5)


class AdminInterfaceTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='staff', password='pass12345', is_staff=True)
        self.client_user = User.objects.create_user(username='client', password='pass12345')

    def test_client_cannot_open_dashboard(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_staff_sees_dedicated_interface(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tableau de bord')
        self.assertContains(response, '/admin/')

    def test_staff_login_redirects_to_dashboard(self):
        response = self.client.post(
            reverse('login'), {'username': 'staff', 'password': 'pass12345'}
        )
        self.assertRedirects(response, reverse('dashboard'))

    def test_client_login_redirects_to_shop(self):
        response = self.client.post(
            reverse('login'), {'username': 'client', 'password': 'pass12345'}
        )
        self.assertRedirects(response, reverse('home'))


class SettingsTests(TestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(username='staff', password='pass12345', is_staff=True)
        self.category = Category.objects.create(name='Réglages')
        self.product = Product.objects.create(
            category=self.category, name='Produit réglage', price=Decimal('100.00'), stock=10
        )

    def tearDown(self):
        cache.clear()

    def _cart(self):
        cart = Cart.objects.create(session_key='settings-session')
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        return cart

    def test_staff_can_change_currency_and_global_discount(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse('dashboard'),
            {
                'site_name': 'Kalos Test',
                'currency': 'USD',
                'shipping_fee': '0',
                'free_shipping_threshold': '100',
                'global_discount': '20',
                'promo_code': 'KALOS10',
                'promo_discount': '10',
                'shop_open': 'on',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(get_value('currency'), 'USD')
        self.assertEqual(get_value('global_discount'), Decimal('20'))
        totals = cart_totals(self._cart())
        self.assertEqual(totals['discount'], Decimal('20.00'))
        self.assertEqual(totals['total'], Decimal('80.00'))

    def test_promo_code_adds_discount(self):
        totals = cart_totals(self._cart(), 'kalos10')
        self.assertTrue(totals['promo_applied'])
        self.assertEqual(totals['discount'], Decimal('10.00'))

    def test_closed_shop_blocks_checkout(self):
        save_values({'shop_open': False})
        client = Client()
        cart = self._cart()
        session = client.session
        session.save()
        client.post(
            reverse('cart_add'),
            {'product_id': self.product.pk, 'quantity': 1, 'next': '/panier/'},
        )
        response = client.post(
            reverse('checkout'),
            {
                'full_name': 'Test',
                'email': 'test@example.com',
                'address': '1 rue Test',
                'city': 'Paris',
                'country': 'France',
            },
        )
        self.assertRedirects(response, reverse('catalog'))
        self.assertEqual(Order.objects.count(), 0)

    def test_client_cannot_save_settings(self):
        client_user = User.objects.create_user(username='client', password='pass12345')
        client = Client()
        client.force_login(client_user)
        response = client.post(reverse('dashboard'), {'currency': 'USD'})
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(get_value('currency'), 'USD')
