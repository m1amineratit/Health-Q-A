"""
Offers management views for admin panel
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from account.pagination import PagePagination
from admin.models import Offer, OfferCategory


@swagger_auto_schema(
    method='get',
    responses={200: openapi.Response("Offers Statistics")}
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def offers_statistics(request):
    """Get offers dashboard statistics"""
    total_offers = Offer.objects.count()
    total_categories = OfferCategory.objects.count()

    return Response({
        "total_offers": total_offers,
        "total_categories": total_categories
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('category', openapi.IN_QUERY, description="Filter by category ID", type=openapi.TYPE_INTEGER),
        openapi.Parameter('search', openapi.IN_QUERY, description="Search by title", type=openapi.TYPE_STRING),
    ],
    responses={200: openapi.Response("Offers List")}
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def offers_list(request):
    """Get paginated offers list"""
    offers = Offer.objects.select_related('category').all().order_by('-published_at')

    # Search
    search = request.query_params.get('search', None)
    if search:
        offers = offers.filter(title__icontains=search)

    # Filter by category
    category_id = request.query_params.get('category', None)
    if category_id:
        offers = offers.filter(category_id=category_id)

    paginator = PagePagination()
    paginated_offers = paginator.paginate_queryset(offers, request)

    data = []
    for offer in paginated_offers:
        data.append({
            "id": offer.id,
            "title": offer.title,
            "short_description": offer.short_description,
            "long_description": offer.long_description,
            "transaction_value": offer.transaction_value,
            "category": {
                "id": offer.category.id,
                "name": offer.category.name
            },
            "logo": offer.logo.url if offer.logo else None,
            "published_at": offer.published_at
        })

    return paginator.get_paginated_response(data)


@swagger_auto_schema(
    method='get',
    responses={200: openapi.Response("Categories List")}
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def categories_list(request):
    """Get all offer categories for dropdown"""
    categories = OfferCategory.objects.all().values('id', 'name').order_by('name')
    return Response(list(categories), status=status.HTTP_200_OK)


create_category_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "name": openapi.Schema(type=openapi.TYPE_STRING, description="Category Name"),
    },
    required=["name"]
)

@swagger_auto_schema(
    method='post',
    request_body=create_category_schema,
    responses={201: openapi.Response("Category Created")}
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_category(request):
    """Add new offer category"""
    name = request.data.get("name")
    
    if not name:
        return Response(
            {"error": "Name is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    category = OfferCategory.objects.create(name=name)

    return Response({
        "status": "success",
        "message": "Category created successfully",
        "category": {
            "id": category.id,
            "name": category.name
        }
    }, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter('title', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Title"),
        openapi.Parameter('short_description', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Short Description"),
        openapi.Parameter('long_description', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Long Description"),
        openapi.Parameter('transaction_value', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Transaction Value (e.g. 10%)"),
        openapi.Parameter('category_id', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=True, description="Category ID"),
        openapi.Parameter('logo', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Logo Image"),
    ],
    responses={201: openapi.Response("Offer Created")}
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_offer(request):
    """Add new offer"""
    # Note: For file uploads, typically we use parsers, but @api_view handles it if request.data is used correctly with form-data
    
    title = request.data.get("title")
    short_desc = request.data.get("short_description")
    long_desc = request.data.get("long_description", "")
    trans_value = request.data.get("transaction_value")
    category_id = request.data.get("category_id")
    logo = request.FILES.get("logo")

    if not all([title, short_desc, trans_value, category_id]):
        return Response(
            {"error": "Title, short description, transaction value and category are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        category = OfferCategory.objects.get(id=category_id)
    except OfferCategory.DoesNotExist:
        return Response(
            {"error": "Category not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    offer = Offer.objects.create(
        title=title,
        short_description=short_desc,
        long_description=long_desc,
        transaction_value=trans_value,
        category=category,
        logo=logo
    )

    return Response({
        "status": "success",
        "message": "Offer created successfully",
        "offer": {
            "id": offer.id,
            "title": offer.title
        }
    }, status=status.HTTP_201_CREATED)
