"""Peuple la boutique avec des catégories et produits de démonstration.

Usage :
    python manage.py seed_data
    python manage.py seed_data --demo-user
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from boutique.models import Category, Product

CATEGORIES = [
    ('Mode', '👗', 'Pièces élégantes pour toutes les occasions.'),
    ('Électronique', '🎧', 'Technologie pratique et design.'),
    ('Maison', '🕯️', 'Pour un intérieur chaleureux.'),
    ('Beauté', '✨', 'Soins et parfums choisis avec soin.'),
    ('Sport', '🧘', 'Bouger en douceur, chaque jour.'),
    ('Livres', '📚', 'Lectures pour nourrir l’esprit.'),
]

PRODUCTS = [
    ('Mode', 'Robe midi Élégance', 'Une coupe fluide et intemporelle.', 'Robe midi en tissu léger, ceinture ajustable et finitions soignées. Idéale du bureau aux soirées.', 89.00, 119.00, 18, 'hit', True),
    ('Mode', 'Sac à main Aurora', 'Le sac qui illumine chaque tenue.', 'Sac structuré en cuir synthétique, bandoulière amovible et multiples compartiments.', 74.50, None, 12, 'new', True),
    ('Mode', 'Chemise en lin naturel', 'Fraîcheur et élégance naturelle.', 'Chemise en lin lavé, coupe détendue et boutons en corozo.', 49.90, None, 25, '', False),
    ('Électronique', 'Écouteurs sans fil Aura', 'Un son clair, partout avec vous.', 'Écouteurs Bluetooth avec réduction de bruit, 30 h d’autonomie et boîtier de charge.', 129.00, 159.00, 20, 'sale', True),
    ('Électronique', 'Montre connectée Pulse', 'Votre quotidien, au poignet.', 'Suivi d’activité, notifications et écran AMOLED. Étanche jusqu’à 5 ATM.', 149.00, None, 9, 'hit', True),
    ('Électronique', 'Enceinte bluetooth Nomade', 'La musique vous suit partout.', 'Enceinte compacte, son puissant, 12 h d’autonomie et connexion Bluetooth 5.3.', 69.90, None, 30, '', False),
    ('Maison', 'Lampe de table Solstice', 'Une lumière douce et chaleureuse.', 'Lampe en métal brossé avec abat-jour lin, intensité réglable par variateur tactile.', 59.00, None, 14, 'new', True),
    ('Maison', 'Coussin velours doré', 'Une touche de douceur dorée.', 'Coussin en velours doux, 45 × 45 cm, avec fermeture éclair discrète.', 24.90, None, 40, '', False),
    ('Maison', 'Set de table en lin', 'Des repas élégants, simplement.', 'Lot de 4 sets de table en lin lavé, faciles à entretenir.', 34.00, None, 22, '', False),
    ('Beauté', 'Sérum éclat botanique', 'Un teint lumineux, naturellement.', 'Sérum léger à l’acide hyaluronique et extrait de rose, 30 ml.', 39.90, 49.90, 35, 'sale', True),
    ('Beauté', 'Parfum Kalos N°1', 'Une signature florale et boisée.', 'Eau de parfum 50 ml : notes de fleur d’oranger, iris et bois de cèdre.', 79.00, None, 16, 'hit', True),
    ('Beauté', 'Baume lèvres Nectar', 'Une hydratation douce et naturelle.', 'Baume nourrissant au beurre de karité et huile d’amande, 15 ml.', 12.90, None, 60, '', False),
    ('Sport', 'Tapis de yoga Harmonie', 'Votre espace de pratique.', 'Tapis antidérapant en TPE, 6 mm d’épaisseur, avec sangle de transport.', 45.00, None, 28, '', False),
    ('Sport', 'Gourde isotherme Active', 'Froide ou chaude, toute la journée.', 'Gourde inox 750 ml, double paroi isotherme, 12 h froid / 8 h chaud.', 29.90, None, 50, 'new', False),
    ('Livres', 'La beauté du quotidien', 'Un guide de vie simple et inspirant.', 'Un livre pour cultiver la confiance en soi et la sérénité au quotidien.', 21.00, None, 32, '', False),
]


class Command(BaseCommand):
    help = 'Crée les catégories et produits de démonstration Kalos Business.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--demo-user',
            action='store_true',
            help='Crée également un compte client de démonstration.',
        )

    def handle(self, *args, **options):
        categories = {}
        for name, icon, description in CATEGORIES:
            category, created = Category.objects.get_or_create(
                slug=slugify(name),
                defaults={'name': name, 'icon': icon, 'description': description},
            )
            categories[name] = category
            self.stdout.write(f"{'Créée' if created else 'Existante'} : {category.name}")

        for category_name, name, short, description, price, old_price, stock, badge, featured in PRODUCTS:
            slug = slugify(name)
            image_url = (
                'https://placehold.co/600x450/1b2c43/c8a13a/png?text='
                + slug.replace('-', '+')
            )
            product, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'category': categories[category_name],
                    'name': name,
                    'short_description': short,
                    'description': description,
                    'price': price,
                    'old_price': old_price,
                    'stock': stock,
                    'image_url': image_url,
                    'badge': badge,
                    'is_featured': featured,
                },
            )
            self.stdout.write(f"{'Créé' if created else 'Existant'} : {product.name}")

        if options['demo_user']:
            user, created = User.objects.get_or_create(
                username='demo',
                defaults={'email': 'demo@kalos.test', 'first_name': 'Client', 'last_name': 'Démo'},
            )
            if created:
                user.set_password('Kalos2026!')
                user.save()
                self.stdout.write(self.style.SUCCESS('Compte démo créé : demo / Kalos2026!'))
            else:
                self.stdout.write('Compte démo déjà présent.')

        self.stdout.write(self.style.SUCCESS('Données de démonstration prêtes.'))
