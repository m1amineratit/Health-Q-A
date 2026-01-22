from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import models
from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Doctor, Establishment
from .serializers import RegisterSerializer, SetPasswordSerializer, AcceptUserSerializer
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
import logging

logger = logging.getLogger(__name__)


# --- SCHEMAS FOR SWAGGER ---

register_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'speciality': openapi.Schema(type=openapi.TYPE_STRING, description='Medical speciality'),
        'full_name': openapi.Schema(type=openapi.TYPE_STRING, description='Full name'),
        'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
        'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number'),
    },
    required=['speciality', 'full_name', 'email', 'phone_number']
)

login_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
        'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
    },
    required=['username', 'password']
)

password_reset_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
    },
    required=['email']
)

password_reset_confirm_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'uid': openapi.Schema(type=openapi.TYPE_STRING, description='User ID (base64 encoded)'),
        'token': openapi.Schema(type=openapi.TYPE_STRING, description='Reset token'),
        'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='New password'),
    },
    required=['uid', 'token', 'new_password']
)

doctor_update_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name'),
        'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name'),
        'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
        'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password (optional)'),
        'speciality': openapi.Schema(type=openapi.TYPE_STRING, description='Medical speciality'),
        'number_of_phone': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number'),
        'instagram_account': openapi.Schema(type=openapi.TYPE_STRING, description='Instagram account handle'),
        'inpe': openapi.Schema(type=openapi.TYPE_STRING, description='INPE number'),
        'ville': openapi.Schema(type=openapi.TYPE_STRING, description='City'),
    }
)

establishment_create_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'establishment_type': openapi.Schema(type=openapi.TYPE_STRING, description='Type of establishment (cabinet, clinic, hospital, laboratory)'),
        'establishment_name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of establishment'),
        'localization': openapi.Schema(type=openapi.TYPE_STRING, description='Google Maps URL'),
        'ville': openapi.Schema(type=openapi.TYPE_STRING, description='City'),
        'commune': openapi.Schema(type=openapi.TYPE_STRING, description='Commune'),
        'quartier': openapi.Schema(type=openapi.TYPE_STRING, description='Quarter/District'),
        'adresse_electronique': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
        'telephone_fixe': openapi.Schema(type=openapi.TYPE_STRING, description='Fixed phone number'),
    },
    required=['establishment_type', 'establishment_name', 'adresse_electronique', 'telephone_fixe', 'ville']
)

establishment_update_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'establishment_type': openapi.Schema(type=openapi.TYPE_STRING, description='Type of establishment'),
        'establishment_name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of establishment'),
        'localization': openapi.Schema(type=openapi.TYPE_STRING, description='Google Maps URL'),
        'ville': openapi.Schema(type=openapi.TYPE_STRING, description='City'),
        'commune': openapi.Schema(type=openapi.TYPE_STRING, description='Commune'),
        'quartier': openapi.Schema(type=openapi.TYPE_STRING, description='Quarter/District'),
        'adresse_electronique': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
        'telephone_fixe': openapi.Schema(type=openapi.TYPE_STRING, description='Fixed phone number'),
    }
)


# -------------------------
# REGISTER API
# -------------------------
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
    # Extract full_name from request and split into first and last name
    full_name = request.data.get("full_name", "").strip()
    
    if not full_name:
        return Response({
            "errors": {"full_name": "Full name is required"}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Split full_name into first and last name
    name_parts = full_name.split(' ', 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    
    # Prepare data for serializer (without full_name)
    data = request.data.copy()
    data['first_name'] = first_name
    data['last_name'] = last_name
    
    # Remove full_name from data as it's not a User field
    if 'full_name' in data:
        data.pop('full_name')
    
    serializer = RegisterSerializer(data=data)
    
    if serializer.is_valid():
        validated_data = serializer.validated_data
        
        # Create user without password (account inactive)
        user = User.objects.create_user(
            username=validated_data["email"],  # Use email as username
            email=validated_data["email"],
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
            "message": "Registration successful! Please wait for admin approval. You'll receive an email with instructions to set your password.",
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


# --- AUTH ENDPOINTS ---

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
    username = request.data.get("username")
    password = request.data.get("password")
    
    user = authenticate(request, username=username, password=password)
    
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


@swagger_auto_schema(
    method='get',
    responses={200: "Doctor Profile"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_doctor_profile_api(request):
    """
    Get Doctor Profile
    Returns complete doctor professional information.
    """
    try:
        doctor = request.user.doctor_profile
    except:
        return Response({
            'error': "User is not a doctor"
        }, status=status.HTTP_403_FORBIDDEN)
    
    return Response({
        "status": "success",
        "doctor": {
            "id": doctor.id,
            "user_id": doctor.user.id,
            "first_name": doctor.user.first_name,
            "last_name": doctor.user.last_name,
            "email": doctor.user.email,
            "speciality": doctor.speciality,
            "phone": doctor.number_of_phone,
            "instagram": doctor.instagram_account,
            "inpe": doctor.inpe,
            "ville": doctor.ville,
            "created_at": doctor.created_at.isoformat(),
        }
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    responses={200: "Doctor Statistics"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_doctor_statistics_api(request):
    """
    Get Doctor Statistics
    Returns statistics about answered questions and total views for the logged-in doctor.
    """
    from api.models import Question
    
    try:
        doctor = request.user.doctor_profile
    except:
        return Response({
            'error': "User is not a doctor"
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get questions answered by this doctor
    answered_questions = Question.objects.filter(
        answered_by=request.user,
        status="answered"
    )
    
    # Calculate statistics
    total_answered = answered_questions.count()
    total_views = answered_questions.aggregate(
        total_views=models.Sum('views_count')
    )['total_views'] or 0
    
    average_views = total_views / total_answered if total_answered > 0 else 0
    
    # Get breakdown by category
    category_stats = []
    categories = answered_questions.values_list('category', flat=True).distinct()
    
    for category in categories:
        category_questions = answered_questions.filter(category=category)
        category_total = category_questions.count()
        category_views = category_questions.aggregate(
            total_views=models.Sum('views_count')
        )['total_views'] or 0
        
        category_stats.append({
            "category": category,
            "questions_answered": category_total,
            "total_views": category_views,
            "average_views": category_views / category_total if category_total > 0 else 0,
        })
    
    return Response({
        "status": "success",
        "statistics": {
            "total_questions_answered": total_answered,
            "total_views": total_views,
            "average_views_per_question": round(average_views, 2),
            "category_breakdown": category_stats,
        }
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='patch',
    request_body=doctor_update_schema,
    responses={
        200: "Doctor Profile Updated",
        400: "Invalid Data",
        403: "User is not a doctor"
    }
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_doctor_api(request):
    """
    Update Doctor Profile (Professional Information)
    Updates doctor's professional information like name, speciality, phone, Instagram, etc.
    """
    try:
        doctor = request.user.doctor_profile
    except:
        return Response({
            'error': "User is not a doctor"
        }, status=status.HTTP_403_FORBIDDEN)
    
    user = request.user
    
    # Update User fields
    if 'first_name' in request.data:
        user.first_name = request.data['first_name']
    if 'last_name' in request.data:
        user.last_name = request.data['last_name']
    if 'email' in request.data:
        user.email = request.data['email']
    if 'password' in request.data and request.data['password']:
        user.set_password(request.data['password'])
    
    user.save()
    
    # Update Doctor fields
    if 'speciality' in request.data:
        doctor.speciality = request.data['speciality']
    if 'number_of_phone' in request.data:
        doctor.number_of_phone = request.data['number_of_phone']
    if 'instagram_account' in request.data:
        doctor.instagram_account = request.data['instagram_account']
    if 'inpe' in request.data:
        doctor.inpe = request.data['inpe']
    if 'ville' in request.data:
        doctor.ville = request.data['ville']
    if 'img' in request.FILES:
        doctor.img = request.FILES['img']
    
    doctor.save()
    
    return Response({
        "status": "success",
        "message": "Doctor profile updated successfully",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.get_full_name(),
            "email": user.email,
            "speciality": doctor.speciality,
            "phone": doctor.number_of_phone,
            "instagram": doctor.instagram_account,
            "inpe": doctor.inpe,
            "ville": doctor.ville,
        }
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    responses={200: "Establishment Profile"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_establishment_profile_api(request):
    """
    Get Establishment Profile
    Returns establishment details.
    """
    try:
        doctor = request.user.doctor_profile
        establishment = doctor.doctor_establishment
    except Doctor.DoesNotExist:
        return Response({
            'error': "User is not a doctor"
        }, status=status.HTTP_403_FORBIDDEN)
    except:
        return Response({
            'error': "Establishment not found. Please create one first."
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        "status": "success",
        "establishment": {
            "id": establishment.id,
            "establishment_type": establishment.establishment_type,
            "establishment_name": establishment.establishment_name,
            "localization": establishment.localization,
            "ville": establishment.ville,
            "commune": establishment.commune,
            "quartier": establishment.quartier,
            "adresse_electronique": establishment.adresse_electronique,
            "telephone_fixe": establishment.telephone_fixe,
            "photo": establishment.photo.url if establishment.photo else None,
            "created_at": establishment.created_at.isoformat(),
        }
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='post',
    request_body=establishment_create_schema,
    responses={
        201: "Establishment Created",
        400: "Invalid Data",
        403: "User is not a doctor",
        409: "Establishment already exists for this doctor"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_establishment_api(request):
    """
    Create Establishment Profile
    Creates a new establishment for the logged-in doctor.
    """
    try:
        doctor = request.user.doctor_profile
    except:
        return Response({
            'error': "User is not a doctor"
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Check if establishment already exists
    if hasattr(doctor, 'doctor_establishment'):
        return Response({
            'error': "Establishment already exists for this doctor. Use update endpoint to modify."
        }, status=status.HTTP_409_CONFLICT)
    
    # Validate required fields
    required_fields = ['establishment_type', 'establishment_name', 'adresse_electronique', 'telephone_fixe', 'ville']
    for field in required_fields:
        if field not in request.data or not request.data[field]:
            return Response({
                'error': f"Missing required field: {field}"
            }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        establishment = Establishment.objects.create(
            doctor=doctor,
            establishment_type=request.data['establishment_type'],
            establishment_name=request.data['establishment_name'],
            localization=request.data.get('localization', ''),
            ville=request.data['ville'],
            commune=request.data.get('commune', ''),
            quartier=request.data.get('quartier', ''),
            adresse_electronique=request.data['adresse_electronique'],
            telephone_fixe=request.data['telephone_fixe'],
        )
        
        if 'photo' in request.FILES:
            establishment.photo = request.FILES['photo']
            establishment.save()
        
        return Response({
            "status": "success",
            "message": "Establishment created successfully",
            "establishment": {
                "id": establishment.id,
                "establishment_type": establishment.establishment_type,
                "establishment_name": establishment.establishment_name,
                "localization": establishment.localization,
                "ville": establishment.ville,
                "commune": establishment.commune,
                "quartier": establishment.quartier,
                "adresse_electronique": establishment.adresse_electronique,
                "telephone_fixe": establishment.telephone_fixe,
                "created_at": establishment.created_at.isoformat(),
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f"Error creating establishment: {str(e)}"
        }, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='patch',
    request_body=establishment_update_schema,
    responses={
        200: "Establishment Updated",
        400: "Invalid Data",
        403: "User is not a doctor",
        404: "Establishment not found"
    }
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_establishment_api(request):
    """
    Update Establishment Information
    Updates establishment details like type, name, location, contact info, etc.
    """
    try:
        doctor = request.user.doctor_profile
        establishment = doctor.doctor_establishment
    except Doctor.DoesNotExist:
        return Response({
            'error': "User is not a doctor"
        }, status=status.HTTP_403_FORBIDDEN)
    except:
        return Response({
            'error': "Establishment not found"
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Update Establishment fields
    if 'establishment_type' in request.data:
        establishment.establishment_type = request.data['establishment_type']
    if 'establishment_name' in request.data:
        establishment.establishment_name = request.data['establishment_name']
    if 'localization' in request.data:
        establishment.localization = request.data['localization']
    if 'ville' in request.data:
        establishment.ville = request.data['ville']
    if 'commune' in request.data:
        establishment.commune = request.data['commune']
    if 'quartier' in request.data:
        establishment.quartier = request.data['quartier']
    if 'adresse_electronique' in request.data:
        establishment.adresse_electronique = request.data['adresse_electronique']
    if 'telephone_fixe' in request.data:
        establishment.telephone_fixe = request.data['telephone_fixe']
    if 'photo' in request.FILES:
        establishment.photo = request.FILES['photo']
    
    establishment.save()
    
    return Response({
        "status": "success",
        "message": "Establishment updated successfully",
        "establishment": {
            "id": establishment.id,
            "establishment_type": establishment.establishment_type,
            "establishment_name": establishment.establishment_name,
            "localization": establishment.localization,
            "ville": establishment.ville,
            "commune": establishment.commune,
            "quartier": establishment.quartier,
            "adresse_electronique": establishment.adresse_electronique,
            "telephone_fixe": establishment.telephone_fixe,
        }
    }, status=status.HTTP_200_OK)

# -------------------------
# ACCEPT USER & SET PASSWORD ENDPOINTS
# -------------------------

accept_user_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
        'action': openapi.Schema(type=openapi.TYPE_STRING, description='accept or reject'),
    },
    required=['user_id', 'action']
)

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
            # Mark user as accepted
            doctor.is_accepted = True
            from django.utils import timezone
            doctor.accepted_at = timezone.now()
            doctor.save()
            
            # Generate password reset token for user to set password
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            uid = urlsafe_base64_encode(str(user.id).encode())
            
            # Create password setup link
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            password_setup_link = f"{frontend_url}/set-password/{uid}/{token}/"
            
            # Send acceptance email asynchronously
            subject = "Your Account Has Been Approved!"
            message = f"""
            Hello {user.get_full_name() or user.username},
            
            Great news! Your doctor account has been approved by our administration team.
            
            To complete your registration and set your password, please click the link below:
            
            {password_setup_link}
            
            This link expires in 24 hours.
            
            Once you've set your password, you'll be able to log in and access your account.
            
            If you have any questions, please contact our support team.
            
            Best regards,
            Medical System Team
            """
            
            # Send email with fail_silently=True to avoid blocking
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
                email_sent = True
            except Exception as e:
                logger.error(f"Error sending acceptance email: {e}")
                email_sent = False
            
            # Return success regardless of email status
            return Response({
                "status": "success",
                "message": f"User {user.get_full_name()} has been accepted." + (" Acceptance email sent." if email_sent else " (Email delivery pending)"),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.get_full_name(),
                    "is_accepted": doctor.is_accepted,
                    "is_active": user.is_active
                }
            }, status=status.HTTP_200_OK)
        
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


set_password_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'password': openapi.Schema(type=openapi.TYPE_STRING, description='New password'),
        'password_confirm': openapi.Schema(type=openapi.TYPE_STRING, description='Password confirmation'),
    },
    required=['password', 'password_confirm']
)

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
    uid = request.data.get("uid")
    token = request.data.get("token")
    
    serializer = SetPasswordSerializer(data=request.data)
    
    if not all([uid, token]):
        return Response({
            "error": "Missing required fields: uid, token"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not serializer.is_valid():
        return Response({
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Decode user ID
        user_id = urlsafe_base64_decode(uid).decode()
        user = User.objects.get(id=user_id)
    except (User.DoesNotExist, ValueError, TypeError):
        return Response({
            "error": "Invalid user ID or token"
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Verify token
    token_generator = PasswordResetTokenGenerator()
    if not token_generator.check_token(user, token):
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
    
    return Response({
        "status": "success",
        "message": "Password set successfully! You can now log in.",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.get_full_name(),
            "is_active": user.is_active
        }
    }, status=status.HTTP_200_OK)