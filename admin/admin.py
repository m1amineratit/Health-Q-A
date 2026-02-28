from django.contrib import admin

# Register your models here.
from admin.models import (
    AdminRole,
    ReferralClick,
    ReferralSignup,
    OfferCategory,
    Offer,
    UserRequest, 
)
from account.models import Doctor, Subscription, Establishment
from api.models import Question, Answer

# admin site customizations
admin.site.site_header = "Health Q&A Administration"
admin.site.site_title = "Health-QA Admin"
admin.site.index_title = "Site Management"


class ReferralClickInline(admin.TabularInline):
    model = ReferralClick
    extra = 0
    readonly_fields = ('ip_address', 'created_at')
    fields = ('ip_address', 'created_at')
    can_delete = False


class ReferralSignupInline(admin.TabularInline):
    model = ReferralSignup
    extra = 0
    readonly_fields = ('doctor', 'created_at')
    fields = ('doctor', 'created_at')
    can_delete = False


@admin.register(AdminRole)
class AdminRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'referral_link', 'views_count', 'invites_count', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'referral_link')
    list_filter = ('role', 'created_at')
    readonly_fields = ('referral_link', 'views_count', 'invites_count', 'created_at')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role')
        }),
        ('Affiliate Link', {
            'fields': ('referral_link',)
        }),
        ('Statistics', {
            'fields': ('views_count', 'invites_count')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    inlines = (ReferralClickInline, ReferralSignupInline)


@admin.register(ReferralClick)
class ReferralClickAdmin(admin.ModelAdmin):
    list_display = ('admin_role', 'ip_address', 'created_at')
    search_fields = ('admin_role__referral_link', 'ip_address')
    list_filter = ('admin_role', 'created_at')
    readonly_fields = ('ip_address', 'user_agent', 'created_at')
    fields = ('admin_role', 'ip_address', 'user_agent', 'created_at')


@admin.register(ReferralSignup)
class ReferralSignupAdmin(admin.ModelAdmin):
    list_display = ('admin_role', 'doctor', 'created_at')
    search_fields = ('admin_role__referral_link', 'doctor__user__username')
    list_filter = ('admin_role', 'created_at')
    readonly_fields = ('created_at',)
    fields = ('admin_role', 'doctor', 'created_at')


class OfferInline(admin.TabularInline):
    model = Offer
    extra = 1
    fields = ('title', 'transaction_value')
    can_delete = True


@admin.register(OfferCategory)
class OfferCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at',)
    fields = ('name', 'created_at')
    inlines = (OfferInline,)


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'transaction_value', 'published_at')
    search_fields = ('title', 'category__name')
    list_filter = ('category', 'published_at')
    readonly_fields = ('published_at',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'category')
        }),
        ('Descriptions', {
            'fields': ('short_description', 'long_description')
        }),
        ('Details', {
            'fields': ('transaction_value', 'logo')
        }),
        ('Timestamps', {
            'fields': ('published_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserRequest)
class UserRequestAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'establishment_type', 'phone', 'email', 'status', 'created_at')
    search_fields = ('full_name', 'email', 'phone')
    list_filter = ('status', 'establishment_type', 'created_at')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Contact Information', {
            'fields': ('full_name', 'email', 'phone')
        }),
        ('Establishment Details', {
            'fields': ('establishment_type',)
        }),
        ('Follow-up', {
            'fields': ('contact_rdv', 'visite')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


class EstablishmentInline(admin.StackedInline):
    model = Establishment
    extra = 0
    fields = ('establishment_name', 'establishment_type', 'ville', 'commune', 'telephone_fixe', 'photo')
    readonly_fields = ('created_at',)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'speciality', 'number_of_phone', 'ville', 'is_accepted', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'number_of_phone')
    list_filter = ('speciality', 'ville', 'is_accepted', 'created_at')
    readonly_fields = ('created_at', 'accepted_at')
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'speciality')
        }),
        ('Contact', {
            'fields': ('number_of_phone', 'instagram_account')
        }),
        ('Location', {
            'fields': ('ville',)
        }),
        ('Professional', {
            'fields': ('inpe',)
        }),
        ('Status', {
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
    inlines = (EstablishmentInline,)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'is_active', 'start_date', 'end_date')
    search_fields = ('user__username', 'user__email')
    list_filter = ('plan', 'is_active')


@admin.register(Establishment)
class EstablishmentAdmin(admin.ModelAdmin):
    list_display = ('establishment_name', 'doctor', 'establishment_type', 'ville', 'telephone_fixe', 'created_at')
    search_fields = ('establishment_name', 'doctor__user__username', 'ville')
    list_filter = ('establishment_type', 'ville', 'created_at')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('establishment_name', 'establishment_type', 'doctor')
        }),
        ('Location', {
            'fields': ('ville', 'commune', 'quartier', 'localization')
        }),
        ('Contact', {
            'fields': ('telephone_fixe', 'adresse_electronique')
        }),
        ('Media', {
            'fields': ('photo',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('instagram_username', 'category', 'status', 'created_at', 'views_count')
    search_fields = ('instagram_username', 'question_text')
    list_filter = ('status', 'category', 'created_at')
    readonly_fields = ('created_at', 'views_count')
    fieldsets = (
        ('Question Details', {
            'fields': ('question_text', 'category')
        }),
        ('Instagram', {
            'fields': ('instagram_username', 'instagram_user_id')
        }),
        ('Assignment', {
            'fields': ('doctor',)
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Analytics', {
            'fields': ('views_count',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'answered_by', 'answer_sent', 'created_at', 'views_count')
    search_fields = ('question__instagram_username', 'answer_text', 'answered_by__username')
    list_filter = ('answer_sent', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'views_count')
    fieldsets = (
        ('Question & Answerer', {
            'fields': ('question', 'answered_by')
        }),
        ('Answer', {
            'fields': ('answer_text',)
        }),
        ('Status', {
            'fields': ('answer_sent',)
        }),
        ('Analytics', {
            'fields': ('views_count',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


