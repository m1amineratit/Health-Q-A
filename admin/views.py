from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny

# Create your views here.

admin_login = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "email": openapi.Schema(type=openapi.TYPE_STRING, description="Admin Email"),
        "password": openapi.Schema(type=openapi.TYPE_STRING, description="Admin Password", format="password")
    }
)

@swagger_auto_schema(
    method='post',
    request_body=admin_login,
    responses={
        200: openapi.Response("Login Successful"),
        401: "Invalid Credentials",
        403: "Unauthorized (Not Admin)"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(request, username=username, password=password)

    if user is None:
        return Response(
            {"error" : "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_staff:
        return Response(
            {"error": "Unauthorized. Admin access only."}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    if not user.is_active:
        return Response({
            "error" : "Account disabled"
        }, status=403)
    
    refresh = RefreshToken.for_user(user)
    
    return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id" : user.id,
                "email" : user.email,
                "username" : user.username,
            }
        })