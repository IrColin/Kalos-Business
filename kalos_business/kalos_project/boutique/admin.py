"""Administration Kalos Business."""

from django.contrib import admin
from django.utils import timezone

from .messaging import send_message
from .models import (
    Cart,
    CartItem,
    Category,
    Message,
    Notification,
    Order,
    Setting,
    OrderItem,
    Product,
    Transaction,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'product_count', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('name', 'unit_price', 'quantity')


class TransactionInline(admin.StackedInline):
    model = Transaction
    extra = 0
    readonly_fields = ('reference', 'provider', 'amount', 'status', 'card_brand', 'card_last4', 'response', 'created_at')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'old_price', 'stock', 'badge', 'is_active', 'is_featured')
    list_filter = ('category', 'is_active', 'is_featured', 'badge')
    search_fields = ('name', 'short_description', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'stock', 'is_active', 'is_featured')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('reference', 'full_name', 'total', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('reference', 'full_name', 'email')
    readonly_fields = ('reference', 'subtotal', 'discount', 'shipping', 'total', 'created_at', 'transaction_ref')
    inlines = [OrderItemInline, TransactionInline]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'order', 'provider', 'amount', 'status', 'created_at')
    list_filter = ('provider', 'status')
    search_fields = ('reference', 'order__reference')
    readonly_fields = ('reference', 'response', 'created_at')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'name', 'email', 'status', 'created_at', 'replied_at')
    list_filter = ('status',)
    search_fields = ('subject', 'name', 'email', 'body')
    readonly_fields = ('thread_token', 'created_at')
    fieldsets = (
        ('Message reçu', {'fields': ('thread_token', 'user', 'name', 'email', 'subject', 'body', 'created_at')}),
        ('Réponse', {'fields': ('reply_text', 'status', 'replied_at')}),
    )
    actions = ['mark_answered', 'mark_closed']

    def save_model(self, request, obj, form, change):
        if obj.reply_text and obj.status == 'answered' and not obj.replied_at:
            obj.replied_at = timezone.now()
        super().save_model(request, obj, form, change)
        if change and 'reply_text' in form.changed_data and obj.reply_text:
            send_message(
                f'Kalos Business — réponse à votre message : {obj.subject}',
                f'Bonjour {obj.name},\n\n{obj.reply_text}\n\n'
                f'Voir la conversation : {request.build_absolute_uri(obj.get_thread_url())}\n\n'
                'L’équipe Kalos Business',
                obj.email,
            )

    @admin.action(description='Marquer comme répondu')
    def mark_answered(self, request, queryset):
        queryset.update(status='answered')

    @admin.action(description='Clôturer les messages')
    def mark_closed(self, request, queryset):
        queryset.update(status='closed')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('title', 'user__username')


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'created_at')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'session_key', 'count', 'updated_at')
    inlines = [CartItemInline]


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'updated_at')
    search_fields = ('key',)
    readonly_fields = ('updated_at',)
