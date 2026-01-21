from django.contrib import admin
from .models import Doctor, Establishment

# Register your models here.

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'speciality', 'number_of_phone', 'ville', 'created_at')
    list_filter = ('speciality', 'ville', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'number_of_phone')
    readonly_fields = ('created_at',)


@admin.register(Establishment)
class EstablishmentAdmin(admin.ModelAdmin):
    list_display = ('establishment_name', 'doctor', 'establishment_type', 'ville', 'created_at')
    list_filter = ('establishment_type', 'ville', 'created_at')
    search_fields = ('establishment_name', 'doctor__user__username', 'adresse_electronique')
    readonly_fields = ('created_at',)

