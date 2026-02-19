# Doctor Profile Endpoints
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import models
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from account.models import Doctor

doctor_update_params = [
    openapi.Parameter('first_name', openapi.IN_FORM, type=openapi.TYPE_STRING, description='First name'),
    openapi.Parameter('last_name', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Last name'),
    openapi.Parameter('email', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Email address'),
    openapi.Parameter('password', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Password (optional)'),
    openapi.Parameter('speciality', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Medical speciality'),
    openapi.Parameter('number_of_phone', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Phone number'),
    openapi.Parameter('instagram_account', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Instagram account handle'),
    openapi.Parameter('inpe', openapi.IN_FORM, type=openapi.TYPE_STRING, description='INPE number'),
    openapi.Parameter('ville', openapi.IN_FORM, type=openapi.TYPE_STRING, description='City'),
    openapi.Parameter('img', openapi.IN_FORM, type=openapi.TYPE_FILE, description='Profile image'),
]


# -------------------------
# GET DOCTOR PROFILE API
# -------------------------
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

    has_establishment = doctor.doctor_establishment.exists()
    
    return Response({
        "status": "success",
        "doctor": {
            "id": doctor.id,
            "user_id": doctor.user.id,
            "first_name": doctor.user.first_name,
            "last_name": doctor.user.last_name,
            "img": doctor.img.url if doctor.img else "https://ik.imagekit.io/brwdo5vcs/OIP.jpg",
            "email": doctor.user.email,
            "speciality": doctor.speciality,
            "phone": doctor.number_of_phone,
            "instagram": doctor.instagram_account,
            "inpe": doctor.inpe,
            "ville": doctor.ville,
            "has_establishment": has_establishment,
            "created_at": doctor.created_at.isoformat(),
        }
    }, status=status.HTTP_200_OK)


# -------------------------
# GET DOCTOR STATISTICS API
# -------------------------
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
        doctor=request.user,
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


# -------------------------
# UPDATE DOCTOR API
# -------------------------
@swagger_auto_schema(
    method='patch',
    manual_parameters=doctor_update_params,
    consumes=['multipart/form-data'],
    responses={
        200: "Doctor Profile Updated",
        400: "Invalid Data",
        403: "User is not a doctor"
    }
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
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
