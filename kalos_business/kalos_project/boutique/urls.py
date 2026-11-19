"""URL de l'application boutique."""
from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('tableau-de-bord/', views.admin_dashboard, name='dashboard'),
    path('boutique/', views.catalog, name='catalog'),
    path('produit/<slug:slug>/', views.product_detail, name='product_detail'),
    path('panier/', views.cart_view, name='cart'),
    path('panier/promo/', views.cart_promo, name='cart_promo'),
    path('panier/ajouter/', views.cart_add, name='cart_add'),
    path('panier/modifier/', views.cart_update, name='cart_update'),
    path('panier/retirer/', views.cart_remove, name='cart_remove'),
    path('commande/', views.checkout, name='checkout'),
    path('paiement/<str:reference>/', views.payment, name='payment'),
    path('confirmation/<str:reference>/', views.payment_success, name='payment_success'),
    path('mes-commandes/', views.my_orders, name='my_orders'),
    path('mes-commandes/<str:reference>/', views.order_detail, name='order_detail'),
    path('contact/', views.contact, name='contact'),
    path('messagerie/<uuid:token>/', views.message_thread, name='message_thread'),
    path('a-propos/', views.about, name='about'),
]
