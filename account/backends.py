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
    message = "This feature requires a premium (pro) subscription. Please upgrade your plan."

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        
        try:
            subscription = user.subscription
        except Exception:
            return False

        return (
            subscription is not None and
            subscription.plan != "free" and
            subscription.is_active
        )