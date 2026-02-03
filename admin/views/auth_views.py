"""
Admin authentication views
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken


admin_login_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "username": openapi.Schema(type=openapi.TYPE_STRING, description="Admin Username"),
        "password": openapi.Schema(type=openapi.TYPE_STRING, description="Admin Password", format="password")
    },
    required=["username", "password"]
)


@swagger_auto_schema(
    method='post',
    request_body=admin_login_schema,
    responses={
        200: openapi.Response("Login Successful"),
        400: "Missing credentials",
        401: "Invalid Credentials",
        403: "Unauthorized (Not Admin)"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login_view(request):
    """Admin login endpoint"""
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response(
            {"error": "Username and password are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(request, username=username, password=password)

    if user is None:
        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_staff:
        return Response(
            {"error": "Unauthorized. Admin access only."},
            status=status.HTTP_403_FORBIDDEN
        )

    if not user.is_active:
        return Response(
            {"error": "Account disabled"},
            status=status.HTTP_403_FORBIDDEN
        )

    refresh = RefreshToken.for_user(user)

    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
        }
    }, status=status.HTTP_200_OK)
