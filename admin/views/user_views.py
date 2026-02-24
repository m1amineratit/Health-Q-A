"""
User management views for admin panel
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.db.models import Q

from account.models import Doctor
from account.pagination import PagePagination
from django.conf import settings


def _absolute_file_url(request, file_field):
    if not file_field:
        return None
    try:
        url = file_field.url
    except Exception:
        return None
    if url.startswith('http'):
        return url
    return request.build_absolute_uri(url)


@swagger_auto_schema(
    method='get',
    responses={200: openapi.Response("Users Statistics")}
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def users_statistics(request):
    """Get users dashboard statistics"""
    total_users = Doctor.objects.count()
    active_users = Doctor.objects.filter(user__is_active=True, is_accepted=True).count()
    quit_users = Doctor.objects.filter(user__is_active=False).count()
    invitations_pending = Doctor.objects.filter(is_accepted=False, user__is_active=False).count()
    verification_pending = Doctor.objects.filter(is_accepted=False).count()

    return Response({
        "total_users": total_users,
        "active_users": active_users,
        "quit_users": quit_users,
        "invitations_pending": invitations_pending,
        "verification_pending": verification_pending
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('search', openapi.IN_QUERY, description="Search by name, email, or phone", type=openapi.TYPE_STRING),
        openapi.Parameter('speciality', openapi.IN_QUERY, description="Filter by speciality", type=openapi.TYPE_STRING),
    ],
    responses={200: openapi.Response("Users List")}
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def users_list(request):
    """Get paginated users list with search and filters"""
    doctors = Doctor.objects.select_related('user').prefetch_related('doctor_establishment')
    
    # Search functionality
    search = request.query_params.get('search', None)
    if search:
        doctors = doctors.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(number_of_phone__icontains=search)
        )
    
    # Filter by speciality
    speciality = request.query_params.get('speciality', None)
    if speciality:
        doctors = doctors.filter(speciality=speciality)
    
    doctors = doctors.order_by('-id')
    
    paginator = PagePagination()
    paginated_doctors = paginator.paginate_queryset(doctors, request)
    
    data = []
    for doctor in paginated_doctors:
        establishments = doctor.doctor_establishment.all()
        
        data.append({
            "id": doctor.id,
            "user_id": doctor.user.id,
            "full_name": f"{doctor.user.first_name} {doctor.user.last_name}",
            "profession": "Médecin",
            "speciality": doctor.get_speciality_display(),
            "establishments": [
                {
                    "id": est.id,
                    "name": est.establishment_name,
                    "type": est.get_establishment_type_display()
                } for est in establishments
            ],
            "email": doctor.user.email,
            "number_of_phone": doctor.number_of_phone,
            "inpe": doctor.inpe,
            "instagram_account": doctor.instagram_account,
            "ville": doctor.ville,
                "photo": _absolute_file_url(request, doctor.img),
            "paiement": "Paid" if doctor.is_accepted else "Pending",
            "is_accepted": doctor.is_accepted,
            "is_active": doctor.user.is_active,
        })
    
    return paginator.get_paginated_response(data)


create_user_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "establishment_type": openapi.Schema(type=openapi.TYPE_STRING, description="Type d'établissement"),
        "full_name": openapi.Schema(type=openapi.TYPE_STRING, description="Nom complet"),
        "phone": openapi.Schema(type=openapi.TYPE_STRING, description="Téléphone portable"),
        "email": openapi.Schema(type=openapi.TYPE_STRING, description="Adresse éléctronique"),
    },
    required=["establishment_type", "full_name", "phone", "email"]
)


@swagger_auto_schema(
    method='post',
    request_body=create_user_schema,
    responses={201: openapi.Response("User Created"), 400: "Invalid Data"}
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_user(request):
    """Create new user (Nouveau utilisateur modal)"""
    full_name = request.data.get("full_name")
    email = request.data.get("email")
    phone = request.data.get("phone")
    establishment_type = request.data.get("establishment_type")
    
    if not all([full_name, email, phone, establishment_type]):
        return Response(
            {"error": "All fields are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user exists
    if User.objects.filter(email=email).exists():
        return Response(
            {"error": "User with this email already exists"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Split name
    names = full_name.strip().split(' ', 1)
    first_name = names[0]
    last_name = names[1] if len(names) > 1 else ''
    
    # Create user
    user = User.objects.create_user(
        username=email,
        email=email,
        first_name=first_name,
        last_name=last_name,
        is_active=False  # Pending approval
    )
    
    # Create doctor profile
    doctor = Doctor.objects.create(
        user=user,
        number_of_phone=phone,
        speciality='generaliste',  # Default
        is_accepted=False
    )
    
    return Response({
        "status": "success",
        "message": "User created successfully",
        "user": {
            "id": doctor.id,
            "full_name": full_name,
            "email": email,
            "phone": phone
        }
    }, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='get',
    responses={200: openapi.Response("User Details")}
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def user_details(request, user_id):
    """Get detailed user information with establishments"""
    try:
        doctor = Doctor.objects.select_related('user').prefetch_related('doctor_establishment').get(id=user_id)
    except Doctor.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    establishments = doctor.doctor_establishment.all()
    
    return Response({
        "user": {
            "id": doctor.id,
            "full_name": f"{doctor.user.first_name} {doctor.user.last_name}",
            "profession": "Médecin",
            "speciality": doctor.get_speciality_display(),
            "email": doctor.user.email,
            "phone": doctor.number_of_phone,
            "instagram": doctor.instagram_account,
            "ville": doctor.ville,
            "inpe": doctor.inpe,
                "photo": _absolute_file_url(request, doctor.img),
            "is_accepted": doctor.is_accepted,
            "is_active": doctor.user.is_active,
        },
        "establishments": [
            {
                "id": est.id,
                "name": est.establishment_name,
                "type": est.get_establishment_type_display(),
                "ville": est.ville,
                "commune": est.commune,
                "quartier": est.quartier,
                "telephone": est.telephone_fixe,
                "email": est.adresse_electronique,
                    "photo": _absolute_file_url(request, est.photo) if hasattr(request, 'build_absolute_uri') else (est.photo.url if est.photo else None),
            } for est in establishments
        ]
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='post',
    responses={200: openapi.Response("User Confirmed")}
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def confirm_user(request, user_id):
    """Confirm user (Confirmer button action)"""
    try:
        doctor = Doctor.objects.get(id=user_id)
    except Doctor.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Accept the doctor
    doctor.is_accepted = True
    from django.utils import timezone
    doctor.accepted_at = timezone.now()
    doctor.save()
    
    # Activate user account
    doctor.user.is_active = True
    doctor.user.save()
    
    return Response({
        "status": "success",
        "message": "User confirmed successfully"
    }, status=status.HTTP_200_OK)


# Legacy endpoint for backward compatibility
@swagger_auto_schema(
    method='get',
    responses={200: openapi.Response("Users Profile")}
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def users_crm(request):
    """Legacy users endpoint - redirects to users_list"""
    base_request = getattr(request, "_request", request)
    return users_list(base_request)
