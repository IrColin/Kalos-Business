"""Modèles métier de la boutique Kalos Business."""

import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


def generate_order_reference():
    """Référence lisible du type KLB-2026-AB12CD."""
    import secrets

    from django.utils import timezone

    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    suffix = ''.join(secrets.choice(alphabet) for _ in range(6))
    return f"KLB-{timezone.localdate().year}-{suffix}"


class Category(models.Model):
    name = models.CharField('Nom', max_length=120, unique=True)
    slug = models.SlugField('Slug', max_length=140, unique=True, blank=True)
    description = models.TextField('Description', blank=True)
    icon = models.CharField('Icône', max_length=32, default='✨', help_text='Emoji affiché sur la carte catégorie.')
    is_active = models.BooleanField('Active', default=True)
    created_at = models.DateTimeField('Créée le', auto_now_add=True)

    class Meta:
        verbose_name = 'Catégorie'
        verbose_name_plural = 'Catégories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def product_count(self):
        return self.products.filter(is_active=True).count()


class Product(models.Model):
    BADGE_CHOICES = [
        ('', 'Aucun'),
        ('new', 'Nouveau'),
        ('sale', 'Promotion'),
        ('hit', 'Best-seller'),
    ]

    category = models.ForeignKey(
        Category, verbose_name='Catégorie', on_delete=models.PROTECT, related_name='products'
    )
    name = models.CharField('Nom', max_length=180)
    slug = models.SlugField('Slug', max_length=200, unique=True, blank=True)
    short_description = models.CharField('Description courte', max_length=255, blank=True)
    description = models.TextField('Description détaillée', blank=True)
    price = models.DecimalField(
        'Prix', max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))]
    )
    old_price = models.DecimalField(
        'Ancien prix', max_digits=10, decimal_places=2, null=True, blank=True
    )
    stock = models.PositiveIntegerField('Stock', default=0)
    image_url = models.URLField('URL de l’image', max_length=500, blank=True)
    badge = models.CharField('Badge', max_length=10, choices=BADGE_CHOICES, blank=True)
    is_active = models.BooleanField('Visible', default=True)
    is_featured = models.BooleanField('À la une', default=False)
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)

    class Meta:
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['is_active', 'is_featured'])]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return int(((self.old_price - self.price) / self.old_price) * 100)
        return 0


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name='cart'
    )
    session_key = models.CharField(max_length=64, null=True, blank=True, unique=True)
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)

    class Meta:
        verbose_name = 'Panier'
        verbose_name_plural = 'Paniers'

    def __str__(self):
        return f'Panier #{self.pk}'

    @property
    def count(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum((item.line_total for item in self.items.all()), Decimal('0.00'))


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, verbose_name='Panier', on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, verbose_name='Produit', on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField('Quantité', default=1)
    created_at = models.DateTimeField('Ajouté le', auto_now_add=True)

    class Meta:
        verbose_name = 'Ligne de panier'
        verbose_name_plural = 'Lignes de panier'
        constraints = [models.UniqueConstraint(fields=['cart', 'product'], name='uniq_cart_product')]

    def __str__(self):
        return f'{self.quantity} × {self.product.name}'

    @property
    def line_total(self):
        return self.product.price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente de paiement'),
        ('paid', 'Payée'),
        ('cod_confirmed', 'Confirmée — paiement à la livraison'),
        ('processing', 'En préparation'),
        ('shipped', 'Expédiée'),
        ('delivered', 'Livrée'),
        ('cancelled', 'Annulée'),
    ]
    PAYMENT_CHOICES = [
        ('card', 'Carte bancaire'),
        ('paypal', 'PayPal'),
        ('cod', 'Paiement à la livraison'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='orders'
    )
    reference = models.CharField('Référence', max_length=32, unique=True, default=generate_order_reference, editable=False)
    full_name = models.CharField('Nom complet', max_length=180)
    email = models.EmailField('E-mail')
    phone = models.CharField('Téléphone', max_length=40, blank=True)
    address = models.CharField('Adresse', max_length=255)
    city = models.CharField('Ville', max_length=120)
    postal_code = models.CharField('Code postal', max_length=20, blank=True)
    country = models.CharField('Pays', max_length=80, default=settings.KALOS_DEFAULT_COUNTRY)
    notes = models.TextField('Notes', blank=True)
    status = models.CharField('Statut', max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField('Moyen de paiement', max_length=20, choices=PAYMENT_CHOICES, blank=True)
    transaction_ref = models.CharField('Référence transaction', max_length=64, blank=True)
    subtotal = models.DecimalField('Sous-total', max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount = models.DecimalField('Réduction', max_digits=10, decimal_places=2, default=Decimal('0.00'))
    shipping = models.DecimalField('Livraison', max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField('Total', max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField('Créée le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifiée le', auto_now=True)
    paid_at = models.DateTimeField('Payée le', null=True, blank=True)

    class Meta:
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['reference']), models.Index(fields=['status'])]

    def __str__(self):
        return self.reference

    @property
    def is_paid(self):
        return self.status in ('paid', 'processing', 'shipped', 'delivered')


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='Commande', on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL, related_name='order_items')
    name = models.CharField('Nom du produit', max_length=180)
    unit_price = models.DecimalField('Prix unitaire', max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField('Quantité')

    class Meta:
        verbose_name = 'Ligne de commande'
        verbose_name_plural = 'Lignes de commande'

    def __str__(self):
        return f'{self.quantity} × {self.name}'

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('succeeded', 'Réussie'),
        ('failed', 'Échouée'),
        ('cod_confirmed', 'Confirmée (livraison)'),
        ('refunded', 'Remboursée'),
    ]

    order = models.OneToOneField(Order, verbose_name='Commande', on_delete=models.CASCADE, related_name='transaction')
    provider = models.CharField('Fournisseur', max_length=30)
    reference = models.CharField('Référence', max_length=64, unique=True)
    amount = models.DecimalField('Montant', max_digits=10, decimal_places=2)
    status = models.CharField('Statut', max_length=20, choices=STATUS_CHOICES, default='pending')
    card_brand = models.CharField('Réseau de carte', max_length=20, blank=True)
    card_last4 = models.CharField('4 derniers chiffres', max_length=4, blank=True)
    response = models.JSONField('Réponse passerelle', default=dict, blank=True)
    created_at = models.DateTimeField('Créée le', auto_now_add=True)

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']

    def __str__(self):
        return self.reference


class Message(models.Model):
    STATUS_CHOICES = [
        ('open', 'Ouvert'),
        ('answered', 'Répondu'),
        ('closed', 'Clôturé'),
    ]

    thread_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='messages'
    )
    name = models.CharField('Nom', max_length=120)
    email = models.EmailField('E-mail')
    subject = models.CharField('Sujet', max_length=180)
    body = models.TextField('Message')
    reply_text = models.TextField('Réponse', blank=True)
    status = models.CharField('Statut', max_length=10, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField('Envoyé le', auto_now_add=True)
    replied_at = models.DateTimeField('Répondu le', null=True, blank=True)

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messagerie'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subject} — {self.name}'

    def get_thread_url(self):
        return reverse('message_thread', args=[str(self.thread_token)])


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField('Titre', max_length=160)
    body = models.TextField('Contenu', blank=True)
    link = models.CharField('Lien', max_length=255, blank=True)
    is_read = models.BooleanField('Lue', default=False)
    created_at = models.DateTimeField('Créée le', auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Setting(models.Model):
    """Valeur de configuration modifiable depuis le tableau de bord."""

    key = models.CharField(max_length=64, unique=True)
    value = models.TextField(blank=True)
    updated_at = models.DateTimeField('Modifiée le', auto_now=True)

    class Meta:
        verbose_name = 'Paramètre'
        verbose_name_plural = 'Paramètres'

    def __str__(self):
        return f'{self.key} = {self.value}'
