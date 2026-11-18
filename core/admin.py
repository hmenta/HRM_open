from django.contrib import admin

from .models import ApiCredential, CompanySettings, EmailSettings, NotificationRule


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ('name', 'tax_id')


@admin.register(EmailSettings)
class EmailSettingsAdmin(admin.ModelAdmin):
    list_display = ('from_email', 'host', 'port', 'updated_at')


@admin.register(ApiCredential)
class ApiCredentialAdmin(admin.ModelAdmin):
    list_display = ('name', 'api_key', 'is_active', 'created_at', 'last_used_at')
    readonly_fields = ('api_key', 'token_hash', 'token_prefix', 'created_at', 'last_used_at')


@admin.register(NotificationRule)
class NotificationRuleAdmin(admin.ModelAdmin):
    list_display = ('event', 'is_active', 'notify_admins', 'notify_operators', 'notify_employee')
