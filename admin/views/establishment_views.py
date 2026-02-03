"""
Establishment management views for admin panel
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from account.models import Establishment
from account.pagination import PagePagination


@swagger_auto_schema(
    method='get',
    responses={200: openapi.Response("Establishments Statistics")}
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def establishments_statistics(request):
    """Get establishments dashboard statistics"""
    total_establishments = Establishment.objects.count()
    active_establishments = Establishment.objects.filter(doctor__is_accepted=True).count()
    pending_establishments = Establishment.objects.filter(doctor__is_accepted=False).count()
    
    # Count by type
    cabinet_count = Establishment.objects.filter(establishment_type='cabinet').count()
    clinic_count = Establishment.objects.filter(establishment_type='clinic').count()
    hospital_count = Establishment.objects.filter(establishment_type='hospital').count()
    
    return Response({
        "total_establishments": total_establishments,
        "active_establishments": active_establishments,
        "pending_establishments": pending_establishments,
        "by_type": {
            "cabinet": cabinet_count,
            "clinic": clinic_count,
            "hospital": hospital_count
        }
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('search', openapi.IN_QUERY, description="Search by name or ville", type=openapi.TYPE_STRING),
        openapi.Parameter('type', openapi.IN_QUERY, description="Filter by establishment type", type=openapi.TYPE_STRING),
    ],
    responses={200: openapi.Response("Establishments List")}
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def establishments_list(request):
    """Get paginated establishments list"""
    establishments = Establishment.objects.select_related('doctor__user').all()
    
    # Search
    search = request.query_params.get('search', None)
    if search:
        establishments = establishments.filter(
            Q(establishment_name__icontains=search) |
            Q(ville__icontains=search) |
            Q(commune__icontains=search)
        )
    
    # Filter by type
    est_type = request.query_params.get('type', None)
    if est_type:
        establishments = establishments.filter(establishment_type=est_type)
    
    establishments = establishments.order_by('-id')
    
    paginator = PagePagination()
    paginated_establishments = paginator.paginate_queryset(establishments, request)
    
    data = []
    for est in paginated_establishments:
        # Count practitioners for this establishment
        practitioners_count = 1  # The owner doctor
        
        data.append({
            "id": est.id,
            "name": est.establishment_name,
            "type": est.get_establishment_type_display(),
            "map": est.localization or "",
            "ville": est.ville,
            "commune": est.commune,
            "quartier": est.quartier,
            "liste_praticiens": practitioners_count,
            "telephone_fixe": est.telephone_fixe,
            "email": est.adresse_electronique,
            "images": est.photo.url if est.photo else None,
            "doctor": {
                "id": est.doctor.id,
                "name": f"{est.doctor.user.first_name} {est.doctor.user.last_name}",
                "speciality": est.doctor.get_speciality_display()
            }
        })
    
    return paginator.get_paginated_response(data)


@swagger_auto_schema(
    method='get',
    responses={200: openapi.Response("Practitioners List")}
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def establishment_practitioners(request, establishment_id):
    """Get list of practitioners for an establishment (Liste des utilisateurs popup)"""
    try:
        establishment = Establishment.objects.select_related('doctor__user').get(id=establishment_id)
    except Establishment.DoesNotExist:
        return Response(
            {"error": "Establishment not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # For now, return the doctor who owns the establishment
    # In the future, this could be expanded to include multiple practitioners
    doctor = establishment.doctor
    
    practitioners = [{
        "id": doctor.id,
        "speciality": doctor.get_speciality_display(),
        "full_name": f"{doctor.user.first_name} {doctor.user.last_name}",
        "phone": doctor.number_of_phone,
    }]
    
    return Response({
        "establishment": {
            "id": establishment.id,
            "name": establishment.establishment_name,
            "type": establishment.get_establishment_type_display()
        },
        "practitioners": practitioners
    }, status=status.HTTP_200_OK)
