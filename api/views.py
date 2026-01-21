import json
import logging
import requests

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Question
from .forms import AnswerForm
from django.http import HttpResponse

logger = logging.getLogger("api")


# ============================================================
# INSTAGRAM WEBHOOK (VERIFY + RECEIVE EVENTS)
# ============================================================
# views.py

def privacy_policy(request):
    return HttpResponse("""
    <html>
    <head><title>Privacy Policy</title></head>
    <body>
        <h1>Privacy Policy</h1>
        <p>This application receives Instagram Direct Messages
        only to provide automated replies.</p>

        <p>We do not sell, share, or store personal data
        beyond what is required to respond to messages.</p>

        <p>Data collected:
        <ul>
            <li>Instagram User ID</li>
            <li>Message content</li>
        </ul>
        </p>

        <p>Data is used only for replying to messages.</p>

        <p>Contact: your@email.com</p>
    </body>
    </html>
    """)

@csrf_exempt
def instagram_webhook(request):
    """
    Instagram webhook endpoint:
    - GET  -> verify webhook
    - POST -> receive DM events
    """
    # -----------------------------
    # VERIFY WEBHOOK
    # -----------------------------
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and token == settings.INSTAGRAM_VERIFY_TOKEN:
            logger.info("Instagram webhook verified")
            return HttpResponse(challenge)

        logger.warning("Instagram webhook verification failed")
        return HttpResponse("Verification failed", status=403)

    # -----------------------------
    # RECEIVE EVENTS
    # -----------------------------
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            logger.info("Webhook received:\n%s", json.dumps(data, indent=2))

            for entry in data.get("entry", []):
                for event in entry.get("messaging", []):
                    process_instagram_message(event)

            return JsonResponse({"status": "ok"})

        except Exception as e:
            logger.error("Webhook processing error", exc_info=True)
            return JsonResponse({"error": str(e)}, status=500)


# ============================================================
# PROCESS INCOMING INSTAGRAM DM
# ============================================================

def process_instagram_message(event):
    """
    Handle a single Instagram DM event
    """
    from .json_api import classify_question
    from .models import Doctor
    
    try:
        print(f"DEBUG: Processing event: {event}")
        
        if "message" not in event:
            print("DEBUG: 'message' key missing")
            logger.info("Non-message event ignored")
            return

        sender_id = event.get("sender", {}).get("id")
        recipient_id = event.get("recipient", {}).get("id")
        message_text = event.get("message", {}).get("text")

        if not sender_id or not message_text:
            logger.warning("Invalid message payload: %s", event)
            return

        # Ignore messages sent by your own page
        if sender_id == settings.INSTAGRAM_PAGE_ID:
            return

        # Sanitize text for logging to prevent emoji crashes
        safe_text = message_text.encode('ascii', 'replace').decode('ascii')
        logger.info(f"Message from {sender_id}: {safe_text}")

        # Get username
        username = get_instagram_username(sender_id) or f"user_{sender_id}"

        # Classify the question based on available doctor specialities
        category = classify_question(message_text)

        # Find a doctor with this speciality to assign the question
        try:
            doctor = Doctor.objects.filter(speciality=category).first()
            doctor_user = doctor.user if doctor else None
        except:
            doctor_user = None

        # Save message as question with category and doctor
        question = Question.objects.create(
            instagram_user_id=sender_id,
            instagram_username=username,
            question_text=message_text,
            category=category,
            doctor=doctor_user,  # Assign doctor with matching speciality
            created_at=timezone.now(),
            status="pending",
        )

        logger.info(f"Question {question.id} created in category: {category}, assigned to doctor: {doctor_user}")

        # Auto reply
        send_instagram_message(
            sender_id,
            "✅ Thanks for your message!\n\nA doctor will review it and reply shortly."
        )

    except Exception:
        logger.error("Error processing Instagram message", exc_info=True)


# ============================================================
# SEND INSTAGRAM MESSAGE
# ============================================================

def send_instagram_message(recipient_id, message_text):
    """
    Send DM via Instagram Messaging API
    """

    url = f"https://graph.facebook.com/v24.0/{settings.INSTAGRAM_PAGE_ID}/messages"
    
    # DEBUG: Log the config being used
    logger.info(f"DEBUG: Attempting to send message")
    logger.info(f"DEBUG: Page ID: {settings.INSTAGRAM_PAGE_ID}")
    logger.info(f"DEBUG: Recipient: {recipient_id}")
    logger.info(f"DEBUG: URL: {url}")
    # logger.info(f"DEBUG: Token: {settings.INSTAGRAM_ACCESS_TOKEN[:10]}...") 

    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text},
    }

    params = {
        "access_token": settings.INSTAGRAM_ACCESS_TOKEN
    }
    print(settings.INSTAGRAM_ACCESS_TOKEN)
    try:
        response = requests.post(url, params=params, json=payload)
        data = response.json()

        if response.status_code == 200:
            logger.info("Message sent to %s", recipient_id)
            return True

        logger.error("Send message failed: %s", data)
        return False

    except Exception:
        logger.error("Send message exception", exc_info=True)
        return False


# ============================================================
# FETCH INSTAGRAM USERNAME
# ============================================================

def get_instagram_username(user_id):
    """
    Fetch IG username using Graph API
    """

    url = f"https://graph.facebook.com/v24.0/{user_id}"
    params = {
        "fields": "username,name",
        "access_token": settings.INSTAGRAM_ACCESS_TOKEN,
    }

    try:
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            return data.get("username") or data.get("name")

        logger.warning("Username fetch failed: %s", response.json())
        return None

    except Exception:
        logger.error("Username fetch error", exc_info=True)
        return None


# ============================================================
# DOCTOR DASHBOARD
# ============================================================

@login_required
def dashboard(request):
    pending_questions = Question.objects.filter(status="pending")
    answered_questions = Question.objects.filter(status="answered").order_by("-answered_at")[:10]

    context = {
        "pending_questions": pending_questions,
        "answered_questions": answered_questions,
        "pending_count": pending_questions.count(),
    }
    return render(request, "qa_system/dashboard.html", context)


# ============================================================
# ANSWER QUESTION
# ============================================================

@login_required
def answer_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)

    if request.method == "POST":
        form = AnswerForm(request.POST, instance=question)
        if form.is_valid():
            question = form.save(commit=False)
            question.answered_by = request.user
            question.answered_at = timezone.now()
            question.status = "answered"
            question.save()

            answer_url = request.build_absolute_uri(
                reverse("public_answer", args=[question.id])
            )

            message = (
                f"👨‍⚕️ Answer from Dr. {request.user.get_full_name() or request.user.username}:\n\n"
                f"{question.answer_text}\n\n"
                f"View full details here: {answer_url}"
            )

            success = send_instagram_message(
                question.instagram_user_id,
                message
            )

            question.answer_sent = success
            question.save()

            return redirect("dashboard")
    else:
        form = AnswerForm(instance=question)

    return render(
        request,
        "qa_system/answer_question.html",
        {"question": question, "form": form}
    )


# ============================================================
# PUBLIC ANSWER PAGE
# ============================================================

def public_answer(request, question_id):
    question = get_object_or_404(
        Question,
        id=question_id,
        status="answered"
    )
    
    # Increment views count
    question.views_count += 1
    question.save(update_fields=['views_count'])

    return render(
        request,
        "qa_system/public_answer.html",
        {"question": question}
    )
