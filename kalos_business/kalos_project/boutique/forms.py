"""Formulaires de la boutique."""

from django import forms

from .app_settings import DEFINITIONS, get_value
from .payments import PAYMENT_METHODS


class BootstrapFormMixin:
    def apply_bootstrap(self):
        for name, field in self.fields.items():
            css = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = (css + ' form-check-input').strip()
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = (css + ' form-select').strip()
            else:
                field.widget.attrs['class'] = (css + ' form-control').strip()
            field.widget.attrs.setdefault('placeholder', field.label)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class CheckoutForm(BootstrapFormMixin, forms.Form):
    full_name = forms.CharField(label='Nom complet', max_length=180)
    email = forms.EmailField(label='Adresse e-mail')
    phone = forms.CharField(label='Téléphone', max_length=40, required=False)
    address = forms.CharField(label='Adresse de livraison', max_length=255)
    city = forms.CharField(label='Ville', max_length=120)
    postal_code = forms.CharField(label='Code postal', max_length=20, required=False)
    country = forms.CharField(
        label='Pays', max_length=80, initial=lambda: get_value('default_country', 'France')
    )
    notes = forms.CharField(
        label='Instructions particulières', required=False, widget=forms.Textarea(attrs={'rows': 3})
    )


class CardPaymentForm(BootstrapFormMixin, forms.Form):
    cardholder = forms.CharField(label='Titulaire de la carte', max_length=120)
    card_number = forms.CharField(
        label='Numéro de carte',
        max_length=23,
        widget=forms.TextInput(attrs={'inputmode': 'numeric', 'autocomplete': 'cc-number'}),
    )
    expiry = forms.CharField(
        label='Expiration',
        max_length=5,
        help_text='MM/AA',
        widget=forms.TextInput(attrs={'placeholder': 'MM/AA', 'autocomplete': 'cc-exp'}),
    )
    cvc = forms.CharField(
        label='CVC',
        max_length=4,
        widget=forms.TextInput(attrs={'inputmode': 'numeric', 'autocomplete': 'cc-csc'}),
    )


class PayPalPaymentForm(BootstrapFormMixin, forms.Form):
    email = forms.EmailField(label='Adresse e-mail PayPal')
    confirm = forms.BooleanField(label='Je confirme le paiement de ma commande', required=True)


class ContactForm(BootstrapFormMixin, forms.Form):
    name = forms.CharField(label='Votre nom', max_length=120)
    email = forms.EmailField(label='Votre e-mail')
    subject = forms.CharField(label='Sujet', max_length=180)
    body = forms.CharField(label='Votre message', widget=forms.Textarea(attrs={'rows': 5}))


class PaymentMethodForm(BootstrapFormMixin, forms.Form):
    method = forms.ChoiceField(
        label='Moyen de paiement',
        choices=[(m['code'], m['label']) for m in PAYMENT_METHODS],
        widget=forms.RadioSelect,
    )


class SettingsForm(BootstrapFormMixin, forms.Form):
    """Formulaire généré à partir des définitions de app_settings."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, definition in DEFINITIONS.items():
            help_text = definition.get('help', '')
            if definition['type'] == 'number':
                field = forms.DecimalField(
                    label=definition['label'], min_value=0, required=False, help_text=help_text
                )
            elif definition['type'] == 'bool':
                field = forms.BooleanField(
                    label=definition['label'], required=False, help_text=help_text
                )
            else:
                field = forms.CharField(
                    label=definition['label'], max_length=255, required=False, help_text=help_text
                )
            field.initial = get_value(key)
            self.fields[key] = field
        self.apply_bootstrap()


class PromoForm(BootstrapFormMixin, forms.Form):
    code = forms.CharField(label='Code promo', max_length=40)
