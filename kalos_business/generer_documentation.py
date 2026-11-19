"""Génère Documentation_Kalos_Business.docx (format Word .docx, sans dépendance)."""

from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

OUTPUT = Path(__file__).resolve().parent / 'Documentation_Kalos_Business.docx'

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def para(text='', style=None, bold=False):
    rpr = '<w:rPr><w:b/></w:rPr>' if bold else ''
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ''
    lines = str(text).split('\n')
    parts = []
    for line in lines:
        parts.append(
            f'<w:p>{ppr}<w:r>{rpr}<w:t xml:space="preserve">{escape(line)}</w:t></w:r></w:p>'
        )
    return ''.join(parts)


def heading1(text):
    return para(text, 'Heading1')


def heading2(text):
    return para(text, 'Heading2')


def title(text):
    return para(text, 'Title')


def bullet(text):
    return para('•  ' + text)


def numbered(index, text):
    return para(f'{index}.  {text}')


def table(rows, widths=None):
    if not rows:
        return ''
    count = len(rows[0])
    widths = widths or [int(9360 / count)] * count
    grid = ''.join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    borders = (
        '<w:tblBorders>'
        + ''.join(
            f'<w:{side} w:val="single" w:sz="6" w:space="0" w:color="B8B8B8"/>'
            for side in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV')
        )
        + '</w:tblBorders>'
    )
    trs = []
    for row in rows:
        cells = []
        for index, cell in enumerate(row):
            width = widths[index] if index < len(widths) else widths[-1]
            cells.append(
                f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/></w:tcPr>'
                f'{para(str(cell))}</w:tc>'
            )
        trs.append('<w:tr>' + ''.join(cells) + '</w:tr>')
    return (
        '<w:tbl><w:tblPr><w:tblW w:w="9360" w:type="dxa"/>'
        + borders
        + '</w:tblPr><w:tblGrid>'
        + grid
        + '</w:tblGrid>'
        + ''.join(trs)
        + '</w:tbl>'
    )


body = []
add = body.append

add(title('Kalos Business'))
add(para('Documentation technique et fonctionnelle de l’application e-commerce', 'Subtitle'))
add(para(f'Version 1.0  |  {date.today().strftime("%d/%m/%Y")}  |  Projet Django 6.1.3'))
add(para(''))
add(heading1('Sommaire'))
for item in [
    '1. Présentation générale',
    '2. Architecture et structure du projet',
    '3. Installation et démarrage',
    '4. Comptes, rôles et sécurité d’accès',
    '5. Parcours client complet',
    '6. Espace administrateur et tableau de bord',
    '7. Paramètres dynamiques de l’application',
    '8. Système de paiement (mode bac à sable et migration API)',
    '9. Messagerie et notifications',
    '10. Modèle de données',
    '11. Commandes utiles et tests',
    '12. Mise en production et dépannage',
    '13. Liste des URL principales',
]:
    add(para(item))

add(heading1('1. Présentation générale'))
add(para(
    'Kalos Business est une boutique en ligne développée avec Django 6.1.3 et Bootstrap 5.3. '
    'Elle permet de vendre des produits en ligne, de gérer un panier, des commandes, des paiements, '
    'une messagerie client et un espace d’administration complet.'
))
add(para(
    'L’application fonctionne sans aucune clé API externe : les paiements sont simulés localement '
    'avec une logique réelle (validation de carte, transaction, stock, confirmation), et la messagerie '
    'utilise la base de données ainsi que le backend e-mail console de Django. Des points d’entrée '
    'sont prévus pour brancher ultérieurement une passerelle de paiement agréée ou un service '
    'de messagerie externe sans modifier les vues ni les templates.'
))
add(para('Fonctionnalités principales :', bold=True))
for feature in [
    'Catalogue avec recherche, catégories, tri et pagination.',
    'Panier persistant (session pour les visiteurs, compte pour les utilisateurs connectés) avec fusion automatique.',
    'Réductions globale et par code promo, configurable depuis le tableau de bord.',
    'Commande, paiement simulé, transaction tracée, décrémentation atomique du stock.',
    'Messagerie avec suivi de conversation et réponse administrateur.',
    'Tableau de bord admin avec statistiques et panneau de paramètres.',
    'Interface responsive Bootstrap 5 avec un thème sobre navy/or',
]:
    add(bullet(feature))

add(heading1('2. Architecture et structure du projet'))
add(para('Racine du projet : C:\\kalos_business'))
add(table([
    ['Chemin', 'Rôle'],
    ['kalos_project/manage.py', 'Point d’entrée des commandes Django.'],
    ['kalos_project/kalos_project/settings.py', 'Configuration Django et constantes par défaut KALOS_*.'],
    ['kalos_project/kalos_project/urls.py', 'URL racine : admin, boutique, connexion, inscription.'],
    ['kalos_project/boutique/models.py', 'Modèles métier : produits, panier, commandes, transactions, messages, paramètres.'],
    ['kalos_project/boutique/views.py', 'Toutes les vues : boutique, panier, commande, paiement, messagerie, dashboard.'],
    ['kalos_project/boutique/urls.py', 'Routes de l’application boutique.'],
    ['kalos_project/boutique/forms.py', 'Formulaires (commande, paiement, contact, paramètres, code promo).'],
    ['kalos_project/boutique/cart.py', 'Logique du panier et calcul des totaux.'],
    ['kalos_project/boutique/payments.py', 'Passerelles de paiement simulées et validation Luhn.'],
    ['kalos_project/boutique/messaging.py', 'Backends de messagerie interchangeables.'],
    ['kalos_project/boutique/app_settings.py', 'Registre et lecture/écriture des paramètres dynamiques.'],
    ['kalos_project/boutique/admin.py', 'Configuration de l’interface d’administration.'],
    ['kalos_project/boutique/templates/boutique/', 'Templates HTML Bootstrap.'],
    ['kalos_project/boutique/static/kalos.css', 'Styles personnalisés (charte navy/or).'],
    ['kalos_project/boutique/management/commands/seed_data.py', 'Génération des données de démonstration.'],
    ['kalos_project/boutique/tests.py', 'Tests automatisés du parcours et des droits.'],
    ['README.md', 'Notice de démarrage et notes techniques.'],
    ['Documentation_Kalos_Business.docx', 'Présent document.'],
], [4300, 5060]))

add(heading1('3. Installation et démarrage'))
add(para('Prérequis : Python 3.10 ou supérieur (testé avec Python 3.15) et Django 6.1.3.'))
add(para('Depuis l’invite PowerShell dans C:\\kalos_business avec l’environnement .kalos activé :'))
add(para('cd kalos_project'))
add(para('python manage.py runserver'))
add(para('Puis ouvrir http://127.0.0.1:8000/ . L’administration Django est sur /admin/ .'))
add(para('Initialisation de la base (déjà effectuée dans le projet livré) :'))
for command in [
    'python manage.py makemigrations boutique',
    'python manage.py migrate',
    'python manage.py seed_data --demo-user',
    'python manage.py createsuperuser',
]:
    add(bullet(command))
add(para(
    'La commande seed_data est idempotente : elle crée 6 catégories, 15 produits et, avec '
    '--demo-user, un compte client de démonstration. Elle peut être relancée sans doublons.'
))

add(heading1('4. Comptes, rôles et sécurité d’accès'))
add(table([
    ['Rôle', 'Identifiant', 'Mot de passe', 'Accès'],
    ['Superutilisateur', 'admin', 'KalosAdmin2026!', 'Tableau de bord + /admin/ + toutes les données.'],
    ['Client démo', 'demo', 'Kalos2026!', 'Boutique, panier, commandes, messagerie.'],
    ['Visiteur', 'aucun', '—', 'Boutique, panier, commande invitée, contact.'],
], [2200, 1800, 2200, 3160]))
add(para(
    'La distinction est fondée sur le champ is_staff. Après connexion, un membre de l’équipe est '
    'redirigé vers /tableau-de-bord/ (vue KalosLoginView) tandis qu’un client retourne à l’accueil. '
    'Le tableau de bord est protégé par user_passes_test(is_staff) : un client qui tente d’y accéder '
    'est redirigé vers la connexion. Les identifiants admin apparaissent dans la navigation '
    '(lien « Administration », badge « Admin », accès à l’interface Django).'
))
add(para(
    'Une commande peut être passée sans compte : elle est alors rattachée à la session via la '
    'référence stockée dans kalos_current_order, ce qui autorise la consultation de la confirmation '
    'et du détail sans exposer les autres commandes.'
))

add(heading1('5. Parcours client complet'))
add(heading2('5.1 Découverte des produits'))
add(para(
    'La page d’accueil présente une bannière, les univers (catégories), les produits à la une '
    'et les nouveautés. La boutique (/boutique/) propose une recherche textuelle (nom, description, '
    'catégorie), un filtre par catégorie, un tri (récent, nom, prix croissant/décroissant) et une '
    'pagination de 9 produits par page. Chaque fiche produit affiche prix, ancien prix, badge, '
    'stock disponible, description et produits similaires.'
))
add(heading2('5.2 Panier et réductions'))
add(para(
    'Le panier est stocké en base (modèles Cart et CartItem). Un visiteur est identifié par sa clé '
    'de session ; lors de la connexion, son panier anonyme est fusionné avec son panier utilisateur. '
    'Les quantités sont plafonnées au stock disponible et une alerte est affichée si la demande '
    'dépasse le stock.'
))
add(para(
    'Le récapitulatif calcule : sous-total, réduction globale (%), réduction du code promo (%), '
    'frais de livraison et total. La livraison devient gratuite lorsque le montant après réduction '
    'atteint le seuil défini dans les paramètres. Le code promo est saisi dans le panier et conservé '
    'en session ; il est retiré automatiquement après paiement.'
))
add(heading2('5.3 Commande et paiement'))
add(para(
    'Le formulaire de commande (/commande/) collecte nom, e-mail, téléphone, adresse, ville, code '
    'postal, pays et notes. Il crée une commande avec une référence unique de type '
    'KLB-2026-XXXXXX et fige les lignes de commande (nom et prix unitaire) pour garantir '
    'l’historique même si le produit est ensuite modifié.'
))
add(para(
    'La page de paiement propose trois moyens : carte bancaire, PayPal et paiement à la livraison. '
    'Après validation, une transaction atomique vérifie à nouveau le stock, le décrémente, met à jour '
    'la commande, crée la Transaction, vide le panier et envoie notification et e-mail. La page de '
    'confirmation affiche le reçu avec référence, montant, moyen de paiement et, le cas échéant, '
    'le réseau de carte et les quatre derniers chiffres.'
))
add(heading2('5.4 Suivi'))
add(para(
    'L’espace « Mes commandes » (réservé aux utilisateurs connectés) liste les commandes avec statut '
    'et permet d’ouvrir le détail. Les visiteurs invités accèdent à leur commande via le lien de '
    'confirmation envoyé par e-mail et la référence conservée en session.'
))

add(heading1('6. Espace administrateur et tableau de bord'))
add(para(
    'Le tableau de bord (/tableau-de-bord/) est l’interface principale de l’équipe. Il contient :'
))
for item in [
    'Indicateurs : chiffre d’affaires des commandes payées, nombre de commandes, commandes en attente, messages ouverts.',
    'Dernières commandes avec statut et bouton de gestion vers l’admin Django.',
    'Messagerie récente avec accès direct à la réponse.',
    'Actions rapides : ajouter un produit, gérer commandes, messages et transactions.',
    'Produits dont le stock est inférieur ou égal à 5 unités.',
    'Panneau de paramètres (section « Paramètres de l’application ») décrit au chapitre suivant.',
]:
    add(bullet(item))
add(para(
    'L’interface Django classique (/admin/) reste disponible pour la gestion fine des objets : '
    'catégories, produits, commandes (avec lignes et transaction en inline), transactions, messages, '
    'notifications, paniers et paramètres. La réponse à un message via l’admin enregistre la date '
    'de réponse et envoie automatiquement un e-mail au client.'
))

add(heading1('7. Paramètres dynamiques de l’application'))
add(para(
    'Les paramètres sont enregistrés dans la table Setting (clé/valeur) et surchargent les '
    'constantes de settings.py. Ils sont lus via un cache mémoire invalidé à chaque enregistrement. '
    'Toute modification est donc appliquée immédiatement sur tout le site : devise affichée, '
    'calcul des réductions et de la livraison, coordonnées, ouverture de la boutique.'
))
add(table([
    ['Clé', 'Libellé', 'Type', 'Valeur initiale', 'Effet'],
    ['site_name', 'Nom du site', 'Texte', 'Kalos Business', 'Titre et navigation.'],
    ['site_tagline', 'Slogan', 'Texte', 'La beauté du quotidien...', 'Accueil, footer, meta description.'],
    ['currency', 'Devise', 'Texte', '€', 'Tous les montants et récapitulatifs.'],
    ['contact_email', 'E-mail de contact', 'Texte', 'contact@kalosbusiness.test', 'Contact et notifications.'],
    ['contact_phone', 'Téléphone', 'Texte', '+33 1 23 45 67 89', 'Footer et page contact.'],
    ['default_country', 'Pays par défaut', 'Texte', 'France', 'Formulaire de commande.'],
    ['shop_open', 'Boutique ouverte', 'Booléen', 'Vrai', 'Si faux, bandeau et blocage de la commande.'],
    ['shipping_fee', 'Frais de livraison', 'Nombre', '5.90', 'Ajouté au total si seuil non atteint.'],
    ['free_shipping_threshold', 'Seuil livraison offerte', 'Nombre', '100.00', 'Montant après réduction déclenchant la gratuité.'],
    ['global_discount', 'Réduction globale (%)', 'Nombre', '0', 'Appliquée à toutes les commandes.'],
    ['promo_code', 'Code promo actif', 'Texte', 'KALOS10', 'Code accepté dans le panier.'],
    ['promo_discount', 'Réduction du code promo (%)', 'Nombre', '10', 'Cumulable avec la réduction globale (max 100 %).'],
], [2100, 2200, 1000, 1900, 2160]))
add(para(
    'Pour modifier un réglage : tableau de bord → section « Paramètres de l’application » → '
    'changer les champs souhaités → « Enregistrer les paramètres ». Les mêmes valeurs sont '
    'consultables et éditables dans /admin/ → « Paramètres ».'
))

add(heading1('8. Système de paiement (mode bac à sable et migration API)'))
add(heading2('8.1 Principe'))
add(para(
    'Aucune clé API n’est nécessaire et aucun appel réseau n’est effectué. La passerelle locale '
    'simule l’autorisation : elle valide les données, génère une référence de transaction, '
    'enregistre le résultat en base et met la commande à jour. Aucun numéro de carte complet n’est '
    'conservé : seuls le réseau détecté (Visa, Mastercard, Amex, UnionPay) et les quatre derniers '
    'chiffres sont stockés dans Transaction.'
))
add(para('Carte de test : 4242 4242 4242 4242 — expiration 12/30 — CVC 123.'))
add(heading2('8.2 Validations effectuées'))
for item in [
    'Algorithme de Luhn (numéro de carte) et longueur comprise entre 13 et 19 chiffres.',
    'Format et antériorité de la date d’expiration (MM/AA).',
    'Cryptogramme de 3 ou 4 chiffres et nom du titulaire (au moins 3 caractères).',
    'Adresse e-mail PayPal et case de confirmation explicite.',
    'Contrôle du stock dans une transaction atomique avant décrémentation.',
    'Contrôle du statut de la commande pour empêcher un double paiement.',
]:
    add(bullet(item))
add(heading2('8.3 Cycle de vie d’une transaction'))
add(para(
    'Une transaction passe de « pending » à « succeeded » (carte ou PayPal) ou '
    '« cod_confirmed » (paiement à la livraison). La commande passe respectivement à « payée » '
    'ou « confirmée — paiement à la livraison », puis peut évoluer vers « en préparation », '
    '« expédiée », « livrée » ou « annulée » depuis l’administration.'
))
add(heading2('8.4 Migration vers une vraie API'))
for index, step in enumerate([
    'Obtenir les identifiants du prestataire (Stripe, PayPal, CMI, Payzone...).',
    'Créer une classe héritant de BaseGateway dans boutique/payments.py et appeler le SDK dans charge(order, **data).',
    'Retourner un dictionnaire avec status, provider, reference, amount, card_brand, card_last4 et message.',
    'Enregistrer la classe dans GATEWAYS et, si besoin, dans PAYMENT_METHODS.',
    'Mettre KALOS_PAYMENT_MODE = "production" dans settings.py et stocker les clés hors du code (variables d’environnement).',
], start=1):
    add(numbered(index, step))
add(para(
    'Les vues, modèles et templates n’ont pas à être modifiés : seule la passerelle change.'
))

add(heading1('9. Messagerie et notifications'))
add(para(
    'Le formulaire de contact crée un Message avec un jeton UUID unique. Un e-mail de confirmation '
    'est envoyé au visiteur avec un lien privé de suivi (/messagerie/<token>/) et un e-mail '
    'd’information est envoyé à l’adresse de contact configurée. Le visiteur peut ajouter une suite '
    'à la conversation ; chaque suite crée un nouveau fil avec son propre lien.'
))
add(para(
    'L’administrateur répond depuis /admin/ → « Messagerie » en renseignant « Réponse » et en '
    'passant le statut à « Répondu ». La date de réponse est renseignée automatiquement et un e-mail '
    'est envoyé au client avec le lien de la conversation.'
))
add(para(
    'boutique/messaging.py définit BaseMessagingBackend et trois implémentations : '
    'DatabaseMessagingBackend (notification en base + e-mail console, utilisé par défaut), '
    'EmailMessagingBackend (e-mail seul) et ConsoleMessagingBackend (affichage console). '
    'Le réglage KALOS_MESSAGING_BACKEND permet de remplacer ce backend par une classe compatible '
    'avec une méthode send(subject, message, recipient, user=None, link="").'
))
add(para(
    'Les notifications internes (modèle Notification) sont créées pour les utilisateurs connectés '
    'lors des événements de commande et sont affichées dans le contexte global des templates.'
))

add(heading1('10. Modèle de données'))
add(table([
    ['Modèle', 'Description', 'Champs notables'],
    ['Category', 'Univers commercial.', 'nom, slug, icône, description, active.'],
    ['Product', 'Article vendu.', 'catégorie, prix, ancien prix, stock, image, badge, à la une.'],
    ['Cart', 'Panier.', 'utilisateur ou clé de session, dates.'],
    ['CartItem', 'Ligne de panier.', 'produit, quantité (unique par panier).'],
    ['Order', 'Commande.', 'référence, client, adresse, statut, sous-total, réduction, livraison, total, transaction.'],
    ['OrderItem', 'Ligne figée de commande.', 'nom, prix unitaire, quantité, produit optionnel.'],
    ['Transaction', 'Paiement enregistré.', 'fournisseur, référence, montant, statut, réseau, 4 derniers chiffres, réponse JSON.'],
    ['Message', 'Fil de messagerie.', 'jeton UUID, nom, e-mail, sujet, corps, réponse, statut.'],
    ['Notification', 'Message interne à un utilisateur.', 'titre, corps, lien, lu.'],
    ['Setting', 'Paramètre dynamique.', 'clé unique, valeur, date de modification.'],
], [1800, 3300, 4260]))

add(heading1('11. Commandes utiles et tests'))
for command in [
    'python manage.py check',
    'python manage.py makemigrations boutique',
    'python manage.py migrate',
    'python manage.py seed_data',
    'python manage.py seed_data --demo-user',
    'python manage.py test boutique',
    'python manage.py createsuperuser',
]:
    add(bullet(command))
add(para(
    'La suite de tests comporte 12 tests : validation Luhn et détection du réseau, respect du stock, '
    'parcours de paiement valide et invalide, droits d’accès au tableau de bord, redirection après '
    'connexion selon le rôle, modification des paramètres, application du code promo et blocage de '
    'la commande lorsque la boutique est fermée.'
))

add(heading1('12. Mise en production et dépannage'))
add(para('Avant mise en ligne :', bold=True))
for item in [
    'Remplacer SECRET_KEY par une valeur secrète longue et aléatoire.',
    'Passer DEBUG à False et renseigner ALLOWED_HOSTS.',
    'Configurer un vrai backend e-mail et un prestataire de paiement agréé.',
    'Servir le site en HTTPS et activer SESSION_COOKIE_SECURE et CSRF_COOKIE_SECURE.',
    'Ne jamais stocker le numéro de carte complet.',
    'Sauvegarder régulièrement db.sqlite3 ou migrer vers PostgreSQL/MySQL.',
]:
    add(bullet(item))
add(para('Problèmes fréquents :', bold=True))
add(table([
    ['Symptôme', 'Cause probable', 'Solution'],
    ['« manage.py n’est pas reconnu »', 'Commande lancée sans python ou depuis le mauvais dossier.', 'cd kalos_project puis python manage.py runserver.'],
    ['Page blanche ou erreur 500', 'Migrations non appliquées.', 'python manage.py migrate puis check.'],
    ['Ancien bandeau affiché', 'Cache du navigateur.', 'Ctrl+F5.'],
    ['Les nouveaux réglages ne s’appliquent pas', 'Cache mémoire des paramètres.', 'Ils sont invalidés automatiquement ; redémarrer le serveur si besoin.'],
    ['Accès refusé au tableau de bord', 'Compte sans is_staff.', 'Utiliser le compte admin ou l’activer dans /admin/.'],
], [3000, 3100, 3260]))

add(heading1('13. Liste des URL principales'))
add(table([
    ['URL', 'Nom', 'Description'],
    ['/', 'home', 'Page d’accueil.'],
    ['/boutique/', 'catalog', 'Catalogue, recherche et filtres.'],
    ['/produit/<slug>/', 'product_detail', 'Fiche produit.'],
    ['/panier/', 'cart', 'Panier et code promo.'],
    ['/panier/ajouter/', 'cart_add', 'Ajout au panier (POST).'],
    ['/panier/promo/', 'cart_promo', 'Application/retrait du code promo (POST).'],
    ['/commande/', 'checkout', 'Informations de livraison.'],
    ['/paiement/<reference>/', 'payment', 'Choix et traitement du paiement.'],
    ['/confirmation/<reference>/', 'payment_success', 'Reçu de commande.'],
    ['/mes-commandes/', 'my_orders', 'Commandes de l’utilisateur connecté.'],
    ['/mes-commandes/<reference>/', 'order_detail', 'Détail d’une commande.'],
    ['/contact/', 'contact', 'Formulaire de messagerie.'],
    ['/messagerie/<token>/', 'message_thread', 'Suivi d’une conversation.'],
    ['/tableau-de-bord/', 'dashboard', 'Espace admin et paramètres.'],
    ['/admin/', '—', 'Interface d’administration Django.'],
    ['/connexion/', 'login', 'Connexion (redirection selon le rôle).'],
    ['/inscription/', 'register', 'Création de compte client.'],
    ['/deconnexion/', 'logout', 'Déconnexion (POST).'],
], [2900, 2000, 4460]))

document_xml = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<w:document xmlns:w="{W}"><w:body>'
    + ''.join(body)
    + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
      '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" '
      'w:header="709" w:footer="709" w:gutter="0"/></w:sectPr>'
      '</w:body></w:document>'
)

styles_xml = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<w:styles xmlns:w="{W}">'
    '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>'
    '<w:sz w:val="22"/></w:rPr></w:rPrDefault></w:docDefaults>'
    '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
    '<w:name w:val="Normal"/><w:pPr><w:spacing w:after="120"/></w:pPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/>'
    '<w:basedOn w:val="Normal"/><w:rPr><w:b/><w:color w:val="101D2E"/><w:sz w:val="56"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/>'
    '<w:basedOn w:val="Normal"/><w:rPr><w:color w:val="A98424"/><w:sz w:val="28"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/>'
    '<w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="280" w:after="140"/></w:pPr>'
    '<w:rPr><w:b/><w:color w:val="101D2E"/><w:sz w:val="32"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/>'
    '<w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="200" w:after="100"/></w:pPr>'
    '<w:rPr><w:b/><w:color w:val="A98424"/><w:sz w:val="26"/></w:rPr></w:style>'
    '</w:styles>'
)

content_types = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
    '</Types>'
)

root_rels = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
    '</Relationships>'
)

document_rels = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    '</Relationships>'
)

with ZipFile(OUTPUT, 'w', ZIP_DEFLATED) as archive:
    archive.writestr('[Content_Types].xml', content_types)
    archive.writestr('_rels/.rels', root_rels)
    archive.writestr('word/document.xml', document_xml)
    archive.writestr('word/styles.xml', styles_xml)
    archive.writestr('word/_rels/document.xml.rels', document_rels)

print(f'Document généré : {OUTPUT}')
