# Authentication Endpoints
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
import logging

from account.models import Doctor
from account.serializers import RegisterSerializer, SetPasswordSerializer, AcceptUserSerializer
from ..schemas import (
    register_schema,
    login_schema,
    password_reset_schema,
    password_reset_confirm_schema,
    accept_user_schema,
    set_password_schema,
)
from ..utils import get_tokens_for_user

logger = logging.getLogger(__name__)


# -------------------------
# REGISTER API
# -------------------------
@swagger_auto_schema(
    method="post",
    request_body=RegisterSerializer,
    responses={
        201: "User Registered Successfully - Pending Admin Approval",
        400: "Invalid Data"
    }
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register_api(request):
    """
    Register a new doctor account.
    User is created without a password and account is inactive until admin approval.
    User will receive an email once their account is accepted with a link to set their password.
    """
    serializer = RegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        validated_data = serializer.validated_data
        
        # Split full_name into first and last name
        full_name = validated_data["full_name"].strip()
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        # Create user without password (account inactive)
        user = User.objects.create_user(
            username=full_name,  # Use full name as username
            first_name=first_name,
            last_name=last_name,
            password=None  # No password yet
        )
        user.is_active = False  # Deactivate until admin approval
        user.save()

        # Create doctor profile
        doctor = Doctor.objects.create(
            user=user,
            speciality=validated_data["speciality"],
            number_of_phone=validated_data["phone_number"]
        )

        return Response({
            "status": "success",
            "message": "Registration successful! Please wait for admin approval.",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.get_full_name(),
                "speciality": validated_data["speciality"],
                "is_active": user.is_active,
                "is_accepted": doctor.is_accepted
            }
        }, status=status.HTTP_201_CREATED)

    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# -------------------------
# LOGIN API
# -------------------------
@swagger_auto_schema(
    method='post',
    request_body=login_schema,
    responses={
        200: openapi.Response("Login Successful"),
        401: "Invalid Credentials"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    """
    Login User
    Authenticates the user and returns JWT tokens.
    """
    email = request.data.get("email")
    password = request.data.get("password")
    
    user = authenticate(request, email=email, password=password)
    
    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.get_full_name()
            }
        })
    else:
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


# -------------------------
# PASSWORD RESET REQUEST API
# -------------------------
@swagger_auto_schema(
    method='post',
    request_body=password_reset_schema,
    responses={
        200: "Password reset email sent",
        404: "User not found"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request_api(request):
    """
    Request Password Reset
    Sends a password reset email with a secure token.
    """
    email = request.data.get("email")
    
    if not email:
        return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Generate token
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    uid = urlsafe_base64_encode(str(user.id).encode())
    
    # Create reset link (you can customize this URL based on your frontend)
    reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/" if hasattr(settings, 'FRONTEND_URL') else f"http://localhost:3000/reset-password/{uid}/{token}/"
    
    # Send email
    subject = "Password Reset Request"
    message = f"""
    Hello {user.get_full_name() or user.username},
    
    We received a request to reset your password. Click the link below to reset it:
    
    {reset_link}
    
    This link expires in 24 hours.
    
    If you didn't request this, please ignore this email.
    
    Best regards,
    Medical System
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        
        return Response({
            "status": "success",
            "message": "Password reset email sent successfully",
            "email": email
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error sending password reset email: {e}")
        return Response({
            "error": "Failed to send email"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -------------------------
# PASSWORD RESET CONFIRM API
# -------------------------
@swagger_auto_schema(
    method='post',
    request_body=password_reset_confirm_schema,
    responses={
        200: "Password reset successful",
        400: "Invalid token or user ID",
        404: "User not found"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm_api(request):
    """
    Confirm Password Reset
    Validates the reset token and sets a new password.
    """
    uid = request.data.get("uid")
    token = request.data.get("token")
    new_password = request.data.get("new_password")
    
    if not all([uid, token, new_password]):
        return Response({
            "error": "Missing required fields: uid, token, new_password"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if len(new_password) < 8:
        return Response({
            "error": "Password must be at least 8 characters long"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Decode user ID
        user_id = urlsafe_base64_decode(uid).decode()
        user = User.objects.get(id=user_id)
    except (User.DoesNotExist, ValueError, TypeError):
        return Response({
            "error": "Invalid user ID"
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Verify token
    token_generator = PasswordResetTokenGenerator()
    if not token_generator.check_token(user, token):
        return Response({
            "error": "Invalid or expired token"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    return Response({
        "status": "success",
        "message": "Password reset successfully. You can now login with your new password."
    }, status=status.HTTP_200_OK)


# -------------------------
# GET CURRENT USER API
# -------------------------
@swagger_auto_schema(
    method='get',
    responses={200: "User Profile"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user_api(request):
    """
    Get Current User (Me)
    Returns details of the currently logged-in user.
    """
    user = request.user
    speciality = user.doctor_profile.speciality if hasattr(user, 'doctor_profile') else None

    return Response({
        "id": user.id,
        "username": user.username,
        "full_name": user.get_full_name(),
        "email": user.email,
        "is_staff": user.is_staff,
        "speciality": speciality,
    })


# -------------------------
# ACCEPT USER API (Admin Only)
# -------------------------
@swagger_auto_schema(
    method='post',
    request_body=accept_user_schema,
    responses={
        200: "User accepted/rejected successfully",
        400: "Invalid data",
        403: "Permission denied - admin only",
        404: "User not found"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_user_api(request):
    """
    Accept or Reject User Registration (Admin Only)
    Admin endpoint to approve or reject pending doctor registrations.
    When accepted, an email is sent with a link for the user to set their password.
    """
    # Check if user is staff/admin
    if not request.user.is_staff:
        return Response({
            "error": "Permission denied. Only administrators can accept users."
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = AcceptUserSerializer(data=request.data)
    
    if serializer.is_valid():
        data = serializer.validated_data
        user_id = data['user_id']
        action = data['action']
        
        try:
            user = User.objects.get(id=user_id)
            doctor = user.doctor_profile
        except User.DoesNotExist:
            return Response({
                "error": "User not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Doctor.DoesNotExist:
            return Response({
                "error": "Doctor profile not found for this user"
            }, status=status.HTTP_404_NOT_FOUND)
        
        if action == 'accept':
            try:
                # Mark user as accepted
                doctor.is_accepted = True
                from django.utils import timezone
                doctor.accepted_at = timezone.now()
                doctor.save()
                
                # Generate password reset token for user to set password
                token_generator = PasswordResetTokenGenerator()
                token = token_generator.make_token(user)
                uid = urlsafe_base64_encode(str(user.id).encode())
                
                # Create password setup link (for manual sharing)
                frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
                password_setup_link = f"{frontend_url}/set-password/{uid}/{token}/"
                
                # Return success with password setup link for manual handling
                return Response({
                    "status": "success",
                    "message": f"User {user.get_full_name()} has been accepted.",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.get_full_name(),
                        "is_accepted": doctor.is_accepted,
                        "is_active": user.is_active
                    },
                    "link" : password_setup_link,
                    "uid" : uid,
                    "token" : token,
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error in accept_user_api: {e}")
                return Response({
                    "error": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        elif action == 'reject':
            # Delete the user and doctor profile
            user.delete()
            
            # Optionally send rejection email before deleting
            # (You might want to send the rejection email before deletion)
            
            return Response({
                "status": "success",
                "message": f"User registration has been rejected and account deleted.",
            }, status=status.HTTP_200_OK)
    
    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# -------------------------
# SET PASSWORD API
# -------------------------
@swagger_auto_schema(
    method='post',
    request_body=set_password_schema,
    responses={
        200: "Password set successfully",
        400: "Invalid data or token expired",
        404: "User not found"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def set_password_api(request):
    """
    Set Password for Accepted User
    Allows accepted users to set their password using the token sent in acceptance email.
    Requires: uid (base64 encoded user ID), token, password, and password_confirm
    """

    serializer = SetPasswordSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Decode user ID
        user_id = urlsafe_base64_decode(serializer.validated_data['uid']).decode()
        user = User.objects.get(id=user_id)
    except (User.DoesNotExist, ValueError, TypeError):
        return Response({
            "error": "Invalid user ID or token"
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Verify token
    token_generator = PasswordResetTokenGenerator()
    if not token_generator.check_token(user, serializer.validated_data['token']):
        return Response({
            "error": "Invalid or expired token"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if user is accepted
    try:
        doctor = user.doctor_profile
        if not doctor.is_accepted:
            return Response({
                "error": "Your account has not been accepted yet"
            }, status=status.HTTP_400_BAD_REQUEST)
    except Doctor.DoesNotExist:
        return Response({
            "error": "Doctor profile not found"
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Set password
    data = serializer.validated_data
    user.set_password(data['password'])
    user.is_active = True  # Activate user after password is set
    user.save()
    
    # Send confirmation email
    subject = "Password Set Successfully"
    message = f"""
    Hello {user.get_full_name() or user.username},
    
    Your password has been set successfully! You can now log in to your account.
    
    Login URL: {getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/login
    
    If you did not set this password, please contact our support team immediately.
    
    Best regards,
    Medical System Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Error sending password confirmation email: {e}")
    
    tokens = get_tokens_for_user(user)

    return Response({
        "status": "success",
        "message": "Password set successfully! You can now log in.",
        "tokens": tokens,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.get_full_name(),
            "is_active": user.is_active,
            "role": "doctor",
        }
    }, status=status.HTTP_200_OK)
