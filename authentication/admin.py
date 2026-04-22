from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.utils import timezone
from .models import ActivationToken, PasswordResetToken


# Unregister default User admin
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """
    Erweiterter User-Admin mit besserer Übersicht
    """
    list_display = [
        'email', 
        'username', 
        'first_name', 
        'last_name', 
        'is_active_badge', 
        'is_staff', 
        'date_joined'
    ]
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    # Keine zusätzlichen Felder nötig - BaseUserAdmin hat bereits alle wichtigen
    # fieldsets können bei Bedarf komplett überschrieben werden
    
    def is_active_badge(self, obj):
        """Badge für aktive/inaktive Benutzer"""
        if obj.is_active:
            return format_html(
                '<span style="color: white; background-color: #28a745; padding: 3px 10px; border-radius: 3px;">✓ Aktiv</span>'
            )
        return format_html(
            '<span style="color: white; background-color: #dc3545; padding: 3px 10px; border-radius: 3px;">✗ Inaktiv</span>'
        )
    is_active_badge.short_description = 'Status'
    
    # Custom Actions
    actions = ['activate_users', 'deactivate_users']
    
    def activate_users(self, request, queryset):
        """Aktiviert ausgewählte Benutzer"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} Benutzer wurden aktiviert.')
    activate_users.short_description = "Ausgewählte Benutzer aktivieren"
    
    def deactivate_users(self, request, queryset):
        """Deaktiviert ausgewählte Benutzer"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} Benutzer wurden deaktiviert.')
    deactivate_users.short_description = "Ausgewählte Benutzer deaktivieren"


@admin.register(ActivationToken)
class ActivationTokenAdmin(admin.ModelAdmin):
    """
    Admin für Aktivierungstokens
    """
    list_display = [
        'user_email',
        'token_preview',
        'created_at',
        'is_valid_badge',
        'expires_at'
    ]
    list_filter = ['created_at']
    search_fields = ['user__email', 'user__username', 'token']
    readonly_fields = ['token', 'created_at', 'expires_at', 'is_valid_display']
    ordering = ['-created_at']
    
    def user_email(self, obj):
        """Zeigt die E-Mail des Benutzers"""
        return obj.user.email
    user_email.short_description = 'Benutzer'
    user_email.admin_order_field = 'user__email'
    
    def token_preview(self, obj):
        """Zeigt einen verkürzten Token"""
        return f"{obj.token[:20]}..." if len(obj.token) > 20 else obj.token
    token_preview.short_description = 'Token'
    
    def expires_at(self, obj):
        """Zeigt wann der Token abläuft"""
        expiry = obj.created_at + timezone.timedelta(hours=24)
        return expiry.strftime('%d.%m.%Y %H:%M:%S')
    expires_at.short_description = 'Läuft ab am'
    
    def is_valid_badge(self, obj):
        """Badge für gültige/abgelaufene Tokens"""
        if obj.is_valid():
            return format_html(
                '<span style="color: white; background-color: #28a745; padding: 3px 10px; border-radius: 3px;">✓ Gültig</span>'
            )
        return format_html(
            '<span style="color: white; background-color: #dc3545; padding: 3px 10px; border-radius: 3px;">✗ Abgelaufen</span>'
        )
    is_valid_badge.short_description = 'Status'
    
    def is_valid_display(self, obj):
        """Zeigt ob Token gültig ist (für Detail-Ansicht)"""
        return obj.is_valid()
    is_valid_display.short_description = 'Ist gültig'
    is_valid_display.boolean = True
    
    # Custom Actions
    actions = ['delete_expired_tokens']
    
    def delete_expired_tokens(self, request, queryset):
        """Löscht abgelaufene Tokens"""
        deleted = 0
        for token in queryset:
            if not token.is_valid():
                token.delete()
                deleted += 1
        self.message_user(request, f'{deleted} abgelaufene Token wurden gelöscht.')
    delete_expired_tokens.short_description = "Abgelaufene Tokens löschen"


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """
    Admin für Password-Reset-Tokens
    """
    list_display = [
        'user_email',
        'token_preview',
        'created_at',
        'used_badge',
        'is_valid_badge',
        'expires_at'
    ]
    list_filter = ['used', 'created_at']
    search_fields = ['user__email', 'user__username', 'token']
    readonly_fields = ['token', 'created_at', 'expires_at', 'is_valid_display']
    ordering = ['-created_at']
    
    def user_email(self, obj):
        """Zeigt die E-Mail des Benutzers"""
        return obj.user.email
    user_email.short_description = 'Benutzer'
    user_email.admin_order_field = 'user__email'
    
    def token_preview(self, obj):
        """Zeigt einen verkürzten Token"""
        return f"{obj.token[:20]}..." if len(obj.token) > 20 else obj.token
    token_preview.short_description = 'Token'
    
    def expires_at(self, obj):
        """Zeigt wann der Token abläuft"""
        expiry = obj.created_at + timezone.timedelta(hours=1)
        return expiry.strftime('%d.%m.%Y %H:%M:%S')
    expires_at.short_description = 'Läuft ab am'
    
    def used_badge(self, obj):
        """Badge für verwendete Tokens"""
        if obj.used:
            return format_html(
                '<span style="color: white; background-color: #6c757d; padding: 3px 10px; border-radius: 3px;">Verwendet</span>'
            )
        return format_html(
            '<span style="color: white; background-color: #007bff; padding: 3px 10px; border-radius: 3px;">Unbenutzt</span>'
        )
    used_badge.short_description = 'Verwendet'
    
    def is_valid_badge(self, obj):
        """Badge für gültige/abgelaufene Tokens"""
        if obj.is_valid():
            return format_html(
                '<span style="color: white; background-color: #28a745; padding: 3px 10px; border-radius: 3px;">✓ Gültig</span>'
            )
        return format_html(
            '<span style="color: white; background-color: #dc3545; padding: 3px 10px; border-radius: 3px;">✗ Abgelaufen</span>'
        )
    is_valid_badge.short_description = 'Status'
    
    def is_valid_display(self, obj):
        """Zeigt ob Token gültig ist (für Detail-Ansicht)"""
        return obj.is_valid()
    is_valid_display.short_description = 'Ist gültig'
    is_valid_display.boolean = True
    
    # Custom Actions
    actions = ['delete_expired_tokens', 'delete_used_tokens']
    
    def delete_expired_tokens(self, request, queryset):
        """Löscht abgelaufene Tokens"""
        deleted = 0
        for token in queryset:
            if not token.is_valid():
                token.delete()
                deleted += 1
        self.message_user(request, f'{deleted} abgelaufene Token wurden gelöscht.')
    delete_expired_tokens.short_description = "Abgelaufene Tokens löschen"
    
    def delete_used_tokens(self, request, queryset):
        """Löscht verwendete Tokens"""
        deleted = queryset.filter(used=True).count()
        queryset.filter(used=True).delete()
        self.message_user(request, f'{deleted} verwendete Token wurden gelöscht.')
    delete_used_tokens.short_description = "Verwendete Tokens löschen"


# Customize Admin Site
admin.site.site_header = "Videoflix Administration" + "\u00A0" * 65 + "by Patrick Schmidt"
admin.site.site_title = "Videoflix Admin"
admin.site.index_title = "Videoflix Admin-Panel"