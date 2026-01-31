# accounts/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from rest_framework.permissions import BasePermission

# EmailBackend is not strictly necessary if we enforce username=email, 
# but we can keep it if we want to allow login by email even if username is different.
# Since we use default User, get_user_model() returns auth.User.
# The previous logic used 'email' field. auth.User has 'email' field.
# It should work.

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = username or kwargs.get('email')
        if email is None or password is None:
            return None
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None


class IsPremiumUser(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return (
            user.is_authenticated and
            hasattr(user, "subscription") and
            user.subscription.plan != "free" and
            user.subscription.is_active
        )