from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.urls import reverse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Question
from account.models import Doctor
from .views import send_instagram_message
import logging
from django.contrib.auth.models import User
from django.db import models
import requests

logger = logging.getLogger(__name__)

# --- SCHEMAS FOR SWAGGER ---

answer_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'answer': openapi.Schema(type=openapi.TYPE_STRING, description='The answer text to send to the user'),
    },
    required=['answer']
)


# --- QUESTION ENDPOINTS ---

def classify_question(question_text):
    specialities = Doctor.objects.values_list('speciality', flat=True).distinct()
    speciality_list = list(specialities)

    if not speciality_list:
        return "generaliste"
    
    url = "https://openrouter.io/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
}
    
    payload = {
        "model": "mistralai/mistral-small-3.2-24b-instruct",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a classifier. "
                    "Classify the question into one of these categories only: "
                    f"{speciality_list}. "
                    "Return only the category name."
                )
            },
            {
                "role": "user",
                "content": question_text
            }
        ],
        "temperature": 0
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        if "choices" in data:
            result = data["choices"][0]["message"]["content"].strip().lower()
            if result not in speciality_list:
                return speciality_list[0] if speciality_list else 'generaliste'
            return result
        else:
            logger.error(f"OpenRouter API error: {data}")
            return speciality_list[0] if speciality_list else 'generaliste'
            
    except Exception as e:
        logger.error(f"Error calling OpenRouter API: {e}")
        return speciality_list[0] if speciality_list else 'generaliste'



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
    Generaliste doctors see all categories except dentist.
    """
    status_filter = request.query_params.get("status")
    
    try:
        doctor = request.user.doctor_profile
        doctor_speciality = doctor.speciality
    except:
        return Response({
            'error' : "User is not a doctor"
        },
        status=status.HTTP_403_FORBIDDEN)
    
    # Generaliste doctors see all categories except dentist
    if doctor_speciality == 'generaliste':
        questions = Question.objects.exclude(category='dentist').order_by("-created_at")
    else:
        # Other specialists see only their own category
        questions = Question.objects.filter(category=doctor_speciality).order_by("-created_at")
    
    if status_filter in ["pending", "answered"]:
        questions = questions.filter(status=status_filter)
        
    data = []
    for q in questions:
        data.append({
            "id": str(q.id),
            "instagram_username": q.instagram_username,
            "question_text": q.question_text,
            "category": q.category,
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


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('page', openapi.IN_QUERY, description="Page number for pagination", type=openapi.TYPE_INTEGER),
        openapi.Parameter('limit', openapi.IN_QUERY, description="Number of items per page", type=openapi.TYPE_INTEGER),
    ],
    responses={200: "List of Answered Questions"}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def answered_questions_feed_api(request):
    """
    Get Answered Questions Feed
    Returns a paginated feed of all answered questions with doctor information.
    Only returns questions that have been answered and sent.
    """
    page = request.query_params.get("page", 1)
    limit = request.query_params.get("limit", 10)
    
    try:
        page = int(page)
        limit = int(limit)
    except (ValueError, TypeError):
        page = 1
        limit = 10
    
    # Ensure reasonable limits
    if limit > 100:
        limit = 100
    if page < 1:
        page = 1
    
    # Get all answered questions with answers that have been sent
    answered_questions = Question.objects.filter(
        status="answered",
        answer_sent=True
    ).select_related('answered_by', 'answered_by__doctor_profile').order_by("-answered_at")
    
    # Calculate pagination
    total_count = answered_questions.count()
    start = (page - 1) * limit
    end = start + limit
    
    questions_page = answered_questions[start:end]
    
    data = []
    for q in questions_page:
        doctor_info = None
        if q.answered_by and hasattr(q.answered_by, 'doctor_profile'):
            doctor = q.answered_by.doctor_profile
            doctor_info = {
                "id": doctor.id,
                "name": q.answered_by.get_full_name(),
                "speciality": doctor.speciality,
                "speciality_display": doctor.get_speciality_display(),
                "phone": doctor.number_of_phone,
                "img": doctor.img.url if doctor.img else None,
            }
        
        data.append({
            "id": str(q.id),
            "question_text": q.question_text,
            "instagram_username": q.instagram_username,
            "category": q.category,
            "answer_text": q.answer_text,
            "answered_at": q.answered_at.isoformat(),
            "created_at": q.created_at.isoformat(),
            "views_count": q.views_count,
            "doctor": doctor_info,
        })
    
    # Calculate pagination info
    total_pages = (total_count + limit - 1) // limit  # Ceiling division
    
    return Response({
        "status": "success",
        "count": len(data),
        "total_count": total_count,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
        "questions": data
    }, status=status.HTTP_200_OK)
