"""
Roles management views for admin panel
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.db import transaction
from account.pagination import PagePagination
from admin.models import AdminRole


@swagger_auto_schema(
    method='get',
    responses={200: openapi.Response("Roles Statistics")}
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def roles_statistics(request):
    """Get roles dashboard statistics"""
    # Counts based on the design image stats (e.g. 2 Admin, 3 Viseur, 3 Affiliation)
    admin_count = AdminRole.objects.filter(role='admin').count()
    viseur_count = AdminRole.objects.filter(role='viseur').count()
    affiliate_count = AdminRole.objects.filter(role='affiliate').count()

    return Response({
        "admin_count": admin_count,
        "viseur_count": viseur_count,
        "affiliate_count": affiliate_count,
        "total_roles": admin_count + viseur_count + affiliate_count
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('role', openapi.IN_QUERY, description="Filter by role (admin, viseur, affiliate)", type=openapi.TYPE_STRING),
    ],
    responses={200: openapi.Response("Roles List")}
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def roles_list(request):
    """Get paginated roles list"""
    roles = AdminRole.objects.select_related('user').all().order_by('-created_at')

    # Filter by role
    role_param = request.query_params.get('role', None)
    if role_param:
        roles = roles.filter(role=role_param)

    paginator = PagePagination()
    paginated_roles = paginator.paginate_queryset(roles, request)

    data = []
    for role in paginated_roles:
        data.append({
            "id": role.id,
            "user_id": role.user.id,
            "full_name": f"{role.user.first_name} {role.user.last_name}",
            "email": role.user.email,
            "role": role.get_role_display(), # Display name like "Admin"
            "role_code": role.role,         # Code like "admin"
            "referral_link": role.referral_link,
            "views_count": role.views_count,
            "invites_count": role.invites_count,
            "created_at": role.created_at
        })

    return paginator.get_paginated_response(data)


create_role_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "full_name": openapi.Schema(type=openapi.TYPE_STRING, description="Nom complet"),
        "email": openapi.Schema(type=openapi.TYPE_STRING, description="Adresse électronique"),
        "role": openapi.Schema(type=openapi.TYPE_STRING, description="Role (admin, viseur, affiliate)"),
        "phone": openapi.Schema(type=openapi.TYPE_STRING, description="Téléphone (optional)"),
    },
    required=["full_name", "email", "role"]
)

@swagger_auto_schema(
    method='post',
    request_body=create_role_schema,
    responses={201: openapi.Response("Role Created"), 400: "Invalid Data"}
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_role(request):
    """Add new admin/role (Nouveau admin modal)"""
    full_name = request.data.get("full_name")
    email = request.data.get("email")
    role_type = request.data.get("role")
    phone = request.data.get("phone", "") # Phone not stored in standard User, might strictly belong to Doctor profile or extend User but for admin role maybe not critical yet.
    # Note: If phone is critical for AdminRole users, we might need a profile or field, but standard User doesn't have it.
    # For now, we'll proceed creating User and AdminRole. If phone is needed, we would need a profile model for admins too.

    if not all([full_name, email, role_type]):
        return Response(
            {"error": "Full name, email and role are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if role_type not in dict(AdminRole.ROLE_CHOICES):
        return Response(
            {"error": "Invalid role type"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(email=email).exists():
         return Response(
            {"error": "User with this email already exists"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():
            # Split name
            names = full_name.strip().split(' ', 1)
            first_name = names[0]
            last_name = names[1] if len(names) > 1 else ''

            # Create User
            # Admins details usually active by default? Or inactive? 
            # Assuming active for now as admin creates them directly.
            # Password? Typically set via email reset or temporary. 
            # We'll set a random unusable password.
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=True
            )
            user.set_unusable_password()
            user.save()

            # Create AdminRole
            admin_role = AdminRole.objects.create(
                user=user,
                role=role_type
            )
            
            # If role is 'admin', should we give is_staff=True?
            # The design says "AdminRole", distinct from Django superuser. 
            # But likely they need login access. `admin_login_view` checks `is_staff`.
            # So if role is 'admin', we probably should set is_staff=True.
            if role_type == 'admin':
                user.is_staff = True
                user.save()

            return Response({
                "status": "success",
                "message": "Role added successfully",
                "data": {
                    "id": admin_role.id,
                    "full_name": full_name,
                    "role": role_type,
                    "email": email,
                    "referral_link": admin_role.referral_link
                }
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
