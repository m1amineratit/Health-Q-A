from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.utils import timezone
from django.urls import reverse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Question
from .views import send_instagram_message
import logging
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

# --- SCHEMAS FOR SWAGGER ---


# -------------------------
# REGISTER API
# -------------------------
@swagger_auto_schema(
    method="post",
    request_body=RegisterSerializer,
    responses={
        201: "User Registered Successfully",
        400: "Invalid Data"
    }
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register_api(request):
    serializer = RegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        data = serializer.validated_data
        user = User.objects.create_user(
            username=data["username"],
            email=data["email"],
            first_name=data["first_name"],
            last_name=data.get("last_name", ""),
            password=data["password"]
        )

        # Generate JWT Tokens immediately
        refresh = RefreshToken.for_user(user)

        return Response({
            "status": "success",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.get_full_name(),
                "email": user.email
            }
        }, status=status.HTTP_201_CREATED)

    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

login_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
        'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
    },
    required=['username', 'password']
)

answer_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'answer': openapi.Schema(type=openapi.TYPE_STRING, description='The answer text to send to the user'),
    },
    required=['answer']
)


# --- AUTH ENDPOINTS ---

@swagger_auto_schema(
    method='post',
    request_body=login_schema,
    responses={
        200: openapi.Response("Login Successful"),
        401: "Invalid Credentials"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    """
    Login User
    Authenticates the user and returns JWT tokens.
    """
    username = request.data.get("username")
    password = request.data.get("password")
    
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.get_full_name()
            }
        })
    else:
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)



@swagger_auto_schema(
    method='get',
    responses={200: "User Profile"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user_api(request):
    """
    Get Current User (Me)
    Returns details of the currently logged-in user.
    """
    user = request.user
    return Response({
        "id": user.id,
        "username": user.username,
        "full_name": user.get_full_name(),
        "email": user.email,
        "is_staff": user.is_staff
    })


# --- QUESTION ENDPOINTS ---

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status (pending|answered)", type=openapi.TYPE_STRING)
    ],
    responses={200: "List of Questions"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_questions_api(request):
    """
    Get List of Questions
    Returns a list of questions, optionally filtered by status.
    """
    status_filter = request.query_params.get("status")
    
    questions = Question.objects.filter(doctor=request.user).order_by("-created_at")
    
    if status_filter in ["pending", "answered"]:
        questions = questions.filter(status=status_filter)
        
    data = []
    for q in questions:
        data.append({
            "id": str(q.id),
            "instagram_username": q.instagram_username,
            "question_text": q.question_text,
            "status": q.status,
            "created_at": q.created_at.isoformat(),
            "answered_at": q.answered_at.isoformat() if q.answered_at else None,
            "answer_text": q.answer_text,
            "answer_sent": q.answer_sent,
        })
        
    return Response({"count": len(data), "questions": data})


@swagger_auto_schema(
    method='get',
    responses={200: "Question Details"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_question_detail_api(request, question_id):
    """
    Get Question Detail
    """
    q = get_object_or_404(Question, id=question_id, doctor=request.user)
    
    data = {
        "id": str(q.id),
        "instagram_username": q.instagram_username,
        "question_text": q.question_text,
        "status": q.status,
        "created_at": q.created_at.isoformat(),
        "answered_at": q.answered_at.isoformat() if q.answered_at else None,
        "answer_text": q.answer_text,
        "answer_sent": q.answer_sent,
        "answered_by": q.answered_by.username if q.answered_by else None
    }
    
    return Response(data)


@swagger_auto_schema(
    method='post',
    request_body=answer_schema,
    responses={
        200: "Answer Submitted",
        400: "Missing Answer Text"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_answer_api(request, question_id):
    """
    Submit Answer
    Saves the answer and sends an Instagram DM.
    """
    answer_text = request.data.get("answer")
    
    if not answer_text:
        return Response({"error": "Answer text is required"}, status=status.HTTP_400_BAD_REQUEST)
        
    question = get_object_or_404(Question, id=question_id, doctor=request.user)
    
    if question.status == "answered":
        return Response({
            "error": "Question already answered"
        }, status=400)
    
    # Update Question
    question.answer_text = answer_text
    question.answered_by = request.user
    question.answered_at = timezone.now()
    question.status = "answered"
    question.save()
    
    # Construct Message
    answer_url = request.build_absolute_uri(
        reverse("public_answer", args=[question.id])
    )
    
    message = (
        f"👨‍⚕️ Answer from Dr. {request.user.get_full_name() or request.user.username}:\n\n"
        f"{question.answer_text}\n\n"
        f"View full details here: {answer_url}"
    )
    
    # Send DM
    success = send_instagram_message(question.instagram_user_id, message)
    
    question.answer_sent = success
    question.save()
    
    return Response({
        "status": "success",
        "message": "Answer saved and sent to Instagram",
        "instagram_sent": success
    })
