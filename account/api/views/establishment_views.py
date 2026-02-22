# Establishment Endpoints
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from account.backends import IsPremiumUser

from account.models import Doctor, Establishment

establishment_create_params = [
    openapi.Parameter('establishment_type', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Type of establishment (cabinet, clinic, hospital, laboratory)', required=True),
    openapi.Parameter('establishment_name', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Name of establishment', required=True),
    openapi.Parameter('localization', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Google Maps URL'),
    openapi.Parameter('ville', openapi.IN_FORM, type=openapi.TYPE_STRING, description='City', required=True),
    openapi.Parameter('commune', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Commune'),
    openapi.Parameter('quartier', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Quarter/District'),
    openapi.Parameter('adresse_electronique', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Email address', required=True),
    openapi.Parameter('telephone_fixe', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Fixed phone number', required=True),
    openapi.Parameter('photo', openapi.IN_FORM, type=openapi.TYPE_FILE, description='Establishment photo'),
]

establishment_update_params = [
    openapi.Parameter('establishment_type', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Type of establishment'),
    openapi.Parameter('establishment_name', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Name of establishment'),
    openapi.Parameter('localization', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Google Maps URL'),
    openapi.Parameter('ville', openapi.IN_FORM, type=openapi.TYPE_STRING, description='City'),
    openapi.Parameter('commune', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Commune'),
    openapi.Parameter('quartier', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Quarter/District'),
    openapi.Parameter('adresse_electronique', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Email address'),
    openapi.Parameter('telephone_fixe', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Fixed phone number'),
    openapi.Parameter('photo', openapi.IN_FORM, type=openapi.TYPE_FILE, description='Establishment photo'),
]


# -------------------------
# GET ESTABLISHMENT PROFILE API
# -------------------------
@swagger_auto_schema(
    method='get',
    responses={200: "Establishment Profile"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPremiumUser])
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


# -------------------------
# CREATE ESTABLISHMENT API
# -------------------------
@swagger_auto_schema(
    method='post',
    manual_parameters=establishment_create_params,
    consumes=['multipart/form-data'],
    responses={
        201: "Establishment Created",
        400: "Invalid Data",
        403: "User is not a doctor",
        409: "Establishment already exists for this doctor"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
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


# -------------------------
# UPDATE ESTABLISHMENT API
# -------------------------
@swagger_auto_schema(
    method='patch',
    manual_parameters=establishment_update_params,
    consumes=['multipart/form-data'],
    responses={
        200: "Establishment Updated",
        400: "Invalid Data",
        403: "User is not a doctor",
        404: "Establishment not found"
    }
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsPremiumUser])
@parser_classes([MultiPartParser, FormParser])
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
