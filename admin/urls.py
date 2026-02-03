from django.urls import path
from . import views

urlpatterns = [
    # Admin Login
    path('login', views.admin_login_view, name='admin_login'),
    
    # Users Management
    path('users/statistics', views.users_statistics, name='users_statistics'),
    path('users', views.users_list, name='users_list'),
    path('users/add', views.create_user, name='create_user'),
    path('users/<int:user_id>', views.user_details, name='user_details'),
    path('users/<int:user_id>/confirm', views.confirm_user, name='confirm_user'),
    
    # Establishments Management
    path('establishments/statistics', views.establishments_statistics, name='establishments_statistics'),
    path('establishments', views.establishments_list, name='establishments_list'),
    path('establishments/<int:establishment_id>/practitioners', views.establishment_practitioners, name='establishment_practitioners'),
    
    # Requests Management
    path('requests', views.requests_list, name='requests_list'),
    path('requests/<int:request_id>/update', views.update_request_status, name='update_request_status'),
    path('requests/<int:request_id>/decline', views.decline_request, name='decline_request'),

    # Roles Management
    path('roles/statistics', views.roles_statistics, name='roles_statistics'),
    path('roles', views.roles_list, name='roles_list'),
    path('roles/add', views.create_role, name='create_role'),

    # Q&A Management
    path('questions/statistics', views.questions_statistics, name='questions_statistics'),
    path('questions', views.questions_list, name='questions_list'),
    path('questions/add', views.create_question, name='create_question'),

    # Offers Management
    path('offers/statistics', views.offers_statistics, name='offers_statistics'),
    path('offers', views.offers_list, name='offers_list'),
    path('offers/categories', views.categories_list, name='categories_list'),
    path('offers/categories/add', views.create_category, name='create_category'),
    path('offers/add', views.create_offer, name='create_offer'),

    # Legacy endpoint
    path('admin-dashboard', views.users_crm, name='dashboard'),
]