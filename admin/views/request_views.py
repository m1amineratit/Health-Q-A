"""
User Requests management views for admin panel
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from account.pagination import PagePagination
from admin.models import UserRequest


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status (pending, declined, confirmed)", type=openapi.TYPE_STRING),
    ],
    responses={200: openapi.Response("Requests List")}
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def requests_list(request):
    """Get paginated user requests list"""
    requests = UserRequest.objects.all().order_by('-created_at')

    # Filter by status
    status_filter = request.query_params.get('status', 'pending')  # Default to pending as per UI usually
    if status_filter and status_filter != 'all':
        requests = requests.filter(status=status_filter)

    paginator = PagePagination()
    paginated_requests = paginator.paginate_queryset(requests, request)

    data = []
    for req in paginated_requests:
        data.append({
            "id": req.id,
            "establishment_type": req.establishment_type,
            "full_name": req.full_name,
            "phone": req.phone,
            "email": req.email,
            "contact_rdv": req.contact_rdv,
            "visite": req.visite,
            "status": req.status,
            "created_at": req.created_at
        })

    return paginator.get_paginated_response(data)


update_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "contact_rdv": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Contact/RDV Checkbox"),
        "visite": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Visite Checkbox"),
    }
)

@swagger_auto_schema(
    method='patch',
    request_body=update_request_schema,
    responses={200: openapi.Response("Request Updated")}
)
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_request_status(request, request_id):
    """Update request checkboxes (Contact/RDV, Visite)"""
    try:
        user_request = UserRequest.objects.get(id=request_id)
    except UserRequest.DoesNotExist:
        return Response(
            {"error": "Request not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    contact_rdv = request.data.get('contact_rdv')
    visite = request.data.get('visite')

    if contact_rdv is not None:
        user_request.contact_rdv = contact_rdv
    
    if visite is not None:
        user_request.visite = visite
        
    user_request.save()

    return Response({
        "status": "success",
        "message": "Request updated successfully",
        "data": {
            "id": user_request.id,
            "contact_rdv": user_request.contact_rdv,
            "visite": user_request.visite
        }
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='post',
    responses={200: openapi.Response("Request Declined")}
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def decline_request(request, request_id):
    """Decline a request"""
    try:
        user_request = UserRequest.objects.get(id=request_id)
    except UserRequest.DoesNotExist:
        return Response(
            {"error": "Request not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    user_request.status = 'declined'
    user_request.save()

    return Response({
        "status": "success",
        "message": "Request declined successfully"
    }, status=status.HTTP_200_OK)
