from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

# Create your views here.

admin_login = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "email": openapi.Schema(type=openapi.TYPE_STRING, description="Admin Email"),
        "password": openapi.Schema(type=openapi.TYPE_STRING, description="Admin Password")
    }
)

@swagger_auto_schema(
    method='post',
    request_body=admin_login,
    responses={
        200: openapi.Response("Login Successful"),
        401: "Invalid Credentials"
    }
)
@api_view(['POST'])
def admin_login_view(request):
    email = request.data.get("email")
    password = request.data.get("password")

    user = authenticate(request, email=email, password=password)

    if user is None:
        return Response(
            {"error" : "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_staff:
        return Response({
            {"error": "Unauthorized. Admin access only."},
        }, status=status.HTTP_403_FORBIDDEN)
    
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