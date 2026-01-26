from django.urls import path
from . import views

urlpatterns = [
    path('admin', views.admin_login_view, name='admin_login'),

    path('admin-dashboard', views.users_crm, name='dashboard'),
]