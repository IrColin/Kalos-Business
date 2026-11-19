# Kalos Business

Boutique e-commerce Django (interface Bootstrap 5) avec paiement en ligne **en mode démonstration** et messagerie intégrée.

## Démarrage

```powershell
cd C:\kalos_business\kalos_project
python manage.py runserver
```

Ouvrez ensuite http://127.0.0.1:8000/

### Comptes disponibles

| Rôle | Identifiant | Mot de passe |
|---|---|---|
| Administrateur / superutilisateur | `admin` | `KalosAdmin2026!` |
| Client de démonstration | `demo` | `Kalos2026!` |

L'administrateur possède une **interface dédiée** : après connexion sur le site, il est redirigé vers `/tableau-de-bord/` (statistiques, commandes, messagerie, stock, accès rapides). Un lien « Administration » apparaît dans la barre de navigation et mène aussi à l'interface Django `/admin/`. Le client ne voit aucun de ces éléments et reste sur la boutique.

Le tableau de bord contient une section **« Paramètres de l'application »** permettant de régler sans toucher au code : nom du site, slogan, devise, coordonnées, pays par défaut, ouverture/fermeture de la boutique, frais de livraison, seuil de livraison offerte, réduction globale, code promo et sa réduction. Les valeurs sont stockées en base et appliquées immédiatement.

La documentation complète est fournie dans `Documentation_Kalos_Business.docx` (elle peut être régénérée avec `python generer_documentation.py`).

## Parcours utilisateur

1. **Boutique** : recherche, filtres par catégorie, tri, pagination, fiches produits.
2. **Panier** : ajout, modification des quantités (limités par le stock), retrait, récapitulatif avec livraison offerte dès 100 €.
3. **Commande** : formulaire de livraison, création d'une commande avec référence unique.
4. **Paiement** : trois boutons réellement fonctionnels :
   - **Carte bancaire** : validation Luhn, expiration, CVC, détection du réseau ; seuls le réseau et les 4 derniers chiffres sont enregistrés.
   - **PayPal** : confirmation explicite avec adresse e-mail.
   - **Paiement à la livraison** : commande confirmée, règlement au moment de la livraison.
5. **Confirmation** : transaction enregistrée, stock décrémenté atomiquement, panier vidé, page de reçu, notification + e-mail envoyés.
6. **Messagerie** : formulaire de contact → message enregistré, e-mail de confirmation, lien privé de suivi de conversation, réponse via l'admin (`Messagerie`).

### Paiement : ça fonctionne, mais sans argent réel

Aucune clé API n'est nécessaire. Les paiements sont **simulés localement** : les boutons, la validation, la création de transaction, la mise à jour du stock et le reçu sont opérationnels, mais **aucun appel réseau n'est effectué et aucun compte n'est débité**. Un bandeau le rappelle sur toutes les pages.

Carte de test : `4242 4242 4242 4242` — expiration `12/30` — CVC `123`.

Pour utiliser une vraie API plus tard :

1. Obtenez les identifiants de votre prestataire (Stripe, PayPal, CMI, Payzone...).
2. Dans `boutique/payments.py`, créez une classe héritant de `BaseGateway` et appelez le SDK du prestataire dans `charge(order, **data)`. Elle doit retourner un dictionnaire avec `status`, `provider`, `reference`, `amount`, `card_brand`, `card_last4`, `message`.
3. Ajoutez la classe au dictionnaire `GATEWAYS` et éventuellement à `PAYMENT_METHODS`.
4. Mettez `KALOS_PAYMENT_MODE = 'production'` dans `kalos_project/settings.py`.

Les vues, modèles et templates n'ont pas à être modifiés.

### Messagerie : backend interchangeable

`boutique/messaging.py` définit `BaseMessagingBackend` et trois implémentations :

- `DatabaseMessagingBackend` (par défaut) : notification en base + e-mail via le backend console.
- `EmailMessagingBackend` : e-mail uniquement.
- `ConsoleMessagingBackend` : affichage console.

Pour brancher SendGrid, Twilio, WhatsApp etc., ajoutez une classe avec une méthode `send(subject, message, recipient, user=None, link='')` puis changez `KALOS_MESSAGING_BACKEND` dans `settings.py`.

Les réponses se donnent dans `/admin/` → **Messagerie**. Le client suit sa conversation via le lien envoyé par e-mail.

## Commandes utiles

```powershell
python manage.py check
python manage.py makemigrations boutique
python manage.py migrate
python manage.py seed_data            # données de démonstration (idempotent)
python manage.py seed_data --demo-user
python manage.py test boutique        # 12 tests : paiement, droits, paramètres, promo...
python manage.py createsuperuser
python generer_documentation.py       # régénère le fichier Word de documentation
```

## Avant la mise en production

- Remplacez `SECRET_KEY`, passez `DEBUG = False`, renseignez `ALLOWED_HOSTS`.
- Configurez un vrai backend e-mail et un prestataire de paiement agréé.
- Utilisez HTTPS et activez les cookies sécurisés (`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`).
- Ne stockez jamais le numéro de carte complet : l'implémentation actuelle ne garde que les 4 derniers chiffres.
