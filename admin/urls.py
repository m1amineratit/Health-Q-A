from django.urls import path
from . import views

urlpatterns = [
    path('login', views.admin_login_view, name='admin_login'),

    path('admin-dashboard', views.users_crm, name='dashboard'),
]