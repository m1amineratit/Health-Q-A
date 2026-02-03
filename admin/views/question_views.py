"""
Q&A management views for admin panel
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from account.pagination import PagePagination
from api.models import Question, Answer


@swagger_auto_schema(
    method='get',
    responses={200: openapi.Response("Questions Statistics")}
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def questions_statistics(request):
    """Get Q&A dashboard statistics"""
    total_questions = Question.objects.count()
    accepted_count = Question.objects.filter(status='answered').count()
    in_progress_count = Question.objects.filter(status='pending').count()
    refused_count = Question.objects.filter(status='archived').count()
    
    total_responses = Answer.objects.count()

    return Response({
        "total_questions": total_questions,
        "accepted_questions": accepted_count,
        "in_progress_questions": in_progress_count,
        "refused_questions": refused_count,
        "total_responses": total_responses
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('search', openapi.IN_QUERY, description="Search by username or question text", type=openapi.TYPE_STRING),
        openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status (pending, answered, archived)", type=openapi.TYPE_STRING),
        openapi.Parameter('category', openapi.IN_QUERY, description="Filter by category/speciality", type=openapi.TYPE_STRING),
    ],
    responses={200: openapi.Response("Questions List")}
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def questions_list(request):
    """Get paginated questions list with details"""
    questions = Question.objects.select_related('doctor', 'answer__answered_by').all().order_by('-created_at')

    # Search
    search = request.query_params.get('search', None)
    if search:
        questions = questions.filter(
            instagram_username__icontains=search) | questions.filter(question_text__icontains=search)

    # Filter by status
    status_param = request.query_params.get('status', None)
    if status_param:
        questions = questions.filter(status=status_param)

    # Filter by category
    category = request.query_params.get('category', None)
    if category:
        questions = questions.filter(category=category)

    paginator = PagePagination()
    paginated_questions = paginator.paginate_queryset(questions, request)

    data = []
    for q in paginated_questions:
        answer_data = None
        if hasattr(q, 'answer'):
            answer_data = {
                "id": q.answer.id,
                "text": q.answer.answer_text,
                "answered_by": q.answer.answered_by.get_full_name() if q.answer.answered_by else "Unknown",
                "created_at": q.answer.created_at
            }

        data.append({
            "id": str(q.id),
            "instagram_username": q.instagram_username,
            "question_text": q.question_text,
            "category": q.category,
            "created_at": q.created_at,
            "status": q.status,
            "views_count": q.views_count,
            "assigned_doctor": q.doctor.get_full_name() if q.doctor else None,
            "answer": answer_data,
            # Fields for design match
            "demandeur_par": q.instagram_username,
            "depuis": q.created_at,
            "envoyer_a": q.doctor.get_full_name() if q.doctor else "Unassigned",
            "etat": q.status,
            "reponse_par": answer_data['answered_by'] if answer_data else "-",
            "ville": "Casablanca", # Placeholder as not in model
            "tel": "-", # Placeholder as not in model
        })

    return paginator.get_paginated_response(data)


create_question_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "instagram_username": openapi.Schema(type=openapi.TYPE_STRING, description="Instagram Username"),
        "question_text": openapi.Schema(type=openapi.TYPE_STRING, description="Question Text"),
        "category": openapi.Schema(type=openapi.TYPE_STRING, description="Category"),
    },
    required=["instagram_username", "question_text"]
)

@swagger_auto_schema(
    method='post',
    request_body=create_question_schema,
    responses={201: openapi.Response("Question Created")}
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_question(request):
    """Add new question manually"""
    username = request.data.get("instagram_username")
    text = request.data.get("question_text")
    category = request.data.get("category", "")

    if not username or not text:
        return Response(
            {"error": "Username and text are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    question = Question.objects.create(
        instagram_username=username,
        question_text=text,
        category=category,
        status='pending'
    )

    return Response({
        "status": "success",
        "message": "Question created successfully",
        "data": {
            "id": str(question.id),
            "instagram_username": question.instagram_username,
            "status": question.status
        }
    }, status=status.HTTP_201_CREATED)
