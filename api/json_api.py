from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.utils import timezone
from django.urls import reverse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Question, Doctor, Establishment
from .views import send_instagram_message
import logging
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
import requests

logger = logging.getLogger(__name__)

# --- SCHEMAS FOR SWAGGER ---


# -------------------------
# REGISTER API
# -------------------------
@swagger_auto_schema(
    method="post",
    request_body=RegisterSerializer,
    responses={
        201: "User Registered Successfully",
        400: "Invalid Data"
    }
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register_api(request):
    serializer = RegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        data = serializer.validated_data
        user = User.objects.create_user(
            username=data["username"],
            email=data["email"],
            first_name=data["first_name"],
            last_name=data.get("last_name", ""),
            password=data["password"],
        )

        Doctor.objects.create(user=user, speciality=data["speciality"])
        # Generate JWT Tokens immediately
        refresh = RefreshToken.for_user(user)

        return Response({
            "status": "success",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.get_full_name(),
                "email": user.email,
                "speciality": data["speciality"]
            }
        }, status=status.HTTP_201_CREATED)

    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

login_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
        'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
    },
    required=['username', 'password']
)

answer_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'answer': openapi.Schema(type=openapi.TYPE_STRING, description='The answer text to send to the user'),
    },
    required=['answer']
)


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


password_reset_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
    },
    required=['email']
)

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


password_reset_confirm_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'uid': openapi.Schema(type=openapi.TYPE_STRING, description='User ID (base64 encoded)'),
        'token': openapi.Schema(type=openapi.TYPE_STRING, description='Reset token'),
        'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='New password'),
    },
    required=['uid', 'token', 'new_password']
)

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
    speciality = user.doctor.speciality if hasattr(user, 'doctor_profile') else None

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
            "img": doctor.img.url if doctor.img else None,
            "created_at": doctor.created_at.isoformat(),
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


# --- QUESTION ENDPOINTS ---

def classify_question(question_text):
    specialities = Doctor.objects.values_list('speciality', flat=True).distinct()
    speciality_list = list(specialities)

    if not speciality_list:
        return "generaliste"
    
    url = "https://openrouter.io/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
}
    
    payload = {
        "model": "mistralai/mistral-small-3.2-24b-instruct",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a classifier. "
                    "Classify the question into one of these categories only: "
                    f"{speciality_list}. "
                    "Return only the category name."
                )
            },
            {
                "role": "user",
                "content": question_text
            }
        ],
        "temperature": 0
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        if "choices" in data:
            result = data["choices"][0]["message"]["content"].strip().lower()
            if result not in speciality_list:
                return speciality_list[0] if speciality_list else 'generaliste'
            return result
        else:
            logger.error(f"OpenRouter API error: {data}")
            return speciality_list[0] if speciality_list else 'generaliste'
            
    except Exception as e:
        logger.error(f"Error calling OpenRouter API: {e}")
        return speciality_list[0] if speciality_list else 'generaliste'



@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status (pending|answered)", type=openapi.TYPE_STRING)
    ],
    responses={200: "List of Questions"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_questions_api(request):
    """
    Get List of Questions
    Returns a list of questions, optionally filtered by status.
    """
    status_filter = request.query_params.get("status")
    
    try:
        doctor = request.user.doctor_profile
        doctor_speciality = doctor.speciality
    except:
        return Response({
            'error' : "User is not a doctor"
        },
        status=status.HTTP_403_FORBIDDEN)
    
    questions = Question.objects.filter(category=doctor_speciality).order_by("-created_at")
    
    if status_filter in ["pending", "answered"]:
        questions = questions.filter(status=status_filter)
        
    data = []
    for q in questions:
        data.append({
            "id": str(q.id),
            "instagram_username": q.instagram_username,
            "question_text": q.question_text,
            "category": q.category,
            "status": q.status,
            "created_at": q.created_at.isoformat(),
            "answered_at": q.answered_at.isoformat() if q.answered_at else None,
            "answer_text": q.answer_text,
            "answer_sent": q.answer_sent,
        })
        
    return Response({"count": len(data), "questions": data})


@swagger_auto_schema(
    method='get',
    responses={200: "Question Details"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_question_detail_api(request, question_id):
    """
    Get Question Detail
    """
    q = get_object_or_404(Question, id=question_id, doctor=request.user)
    
    data = {
        "id": str(q.id),
        "instagram_username": q.instagram_username,
        "question_text": q.question_text,
        "status": q.status,
        "created_at": q.created_at.isoformat(),
        "answered_at": q.answered_at.isoformat() if q.answered_at else None,
        "answer_text": q.answer_text,
        "answer_sent": q.answer_sent,
        "answered_by": q.answered_by.username if q.answered_by else None
    }
    
    return Response(data)


@swagger_auto_schema(
    method='post',
    request_body=answer_schema,
    responses={
        200: "Answer Submitted",
        400: "Missing Answer Text"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_answer_api(request, question_id):
    """
    Submit Answer
    Saves the answer and sends an Instagram DM.
    """
    answer_text = request.data.get("answer")
    
    if not answer_text:
        return Response({"error": "Answer text is required"}, status=status.HTTP_400_BAD_REQUEST)
        
    question = get_object_or_404(Question, id=question_id, doctor=request.user)
    
    if question.status == "answered":
        return Response({
            "error": "Question already answered"
        }, status=400)
    
    # Update Question
    question.answer_text = answer_text
    question.answered_by = request.user
    question.answered_at = timezone.now()
    question.status = "answered"
    question.save()
    
    # Construct Message
    answer_url = request.build_absolute_uri(
        reverse("public_answer", args=[question.id])
    )
    
    message = (
        f"👨‍⚕️ Answer from Dr. {request.user.get_full_name() or request.user.username}:\n\n"
        f"{question.answer_text}\n\n"
        f"View full details here: {answer_url}"
    )
    
    # Send DM
    success = send_instagram_message(question.instagram_user_id, message)
    
    question.answer_sent = success
    question.save()
    
    return Response({
        "status": "success",
        "message": "Answer saved and sent to Instagram",
        "instagram_sent": success
    })
