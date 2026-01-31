from django.contrib import admin
from .models import Doctor, Subscription, Establishment
from django.contrib.auth.models import User


# Register your models here.

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'speciality', 'is_accepted', 'number_of_phone', 'ville', 'created_at')
    list_filter = ('speciality', 'is_accepted', 'ville', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'number_of_phone')
    readonly_fields = ('created_at', 'accepted_at')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'speciality')
        }),
        ('Contact Information', {
            'fields': ('number_of_phone', 'instagram_account')
        }),
        ('Location', {
            'fields': ('ville',)
        }),
        ('Professional Information', {
            'fields': ('inpe',)
        }),
        ('Acceptance Status', {
            'fields': ('is_accepted', 'accepted_at')
        }),
        ('Media', {
            'fields': ('img',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Establishment)
class EstablishmentAdmin(admin.ModelAdmin):
    list_display = ('establishment_name', 'doctor', 'establishment_type', 'ville', 'created_at')
    list_filter = ('establishment_type', 'ville', 'created_at')
    search_fields = ('establishment_name', 'doctor__user__username', 'adresse_electronique')
    readonly_fields = ('created_at',)

