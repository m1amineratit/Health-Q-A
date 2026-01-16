import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Question

class QuestionModelTest(TestCase):
    def test_create_question(self):
        """Test Question model creation defaults"""
        q = Question.objects.create(
            instagram_user_id="12345",
            instagram_username="test_user",
            question_text="Hello Doc?"
        )
        self.assertEqual(q.status, "pending")
        self.assertFalse(q.answer_sent)
        self.assertIsNotNone(q.created_at)

class AuthApiTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='doc', password='password123')
        self.login_url = reverse('api_login')
        self.me_url = reverse('api_me')

    def get_jwt_token(self, user):
        """Helper method to get JWT access token for a user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_login_success(self):
        response = self.client.post(
            self.login_url,
            json.dumps({'username': 'doc', 'password': 'password123'}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('access', data)
        self.assertIn('refresh', data)
        self.assertIn('user', data)

    def test_login_failure(self):
        response = self.client.post(
            self.login_url,
            json.dumps({'username': 'doc', 'password': 'wrong'}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)

    def test_get_me_authorized(self):
        token = self.get_jwt_token(self.user)
        response = self.client.get(
            self.me_url,
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['username'], 'doc')

    def test_get_me_unauthorized(self):
        """Test that accessing /me without token returns 401"""
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, 401)

class QuestionApiTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='doc', password='password123')
        self.token = str(RefreshToken.for_user(self.user).access_token)
        
        self.question = Question.objects.create(
            instagram_user_id="111",
            instagram_username="patient_zero",
            question_text="Am I sick?",
            doctor=self.user
        )
        
        self.list_url = reverse('api_get_questions')
        self.answer_url = reverse('api_submit_answer', args=[self.question.id])

    def test_get_questions(self):
        response = self.client.get(
            self.list_url,
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['questions'][0]['question_text'], "Am I sick?")

    @patch('api.json_api.send_instagram_message')
    def test_submit_answer(self, mock_send):
        """Test submitting answer calls Instagram API mock"""
        mock_send.return_value = True
        
        payload = {"answer": "You are fine."}
        response = self.client.post(
            self.answer_url,
            json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Reload from DB
        self.question.refresh_from_db()
        self.assertEqual(self.question.status, "answered")
        self.assertEqual(self.question.answer_text, "You are fine.")
        self.assertTrue(self.question.answer_sent)
        
        # Verify Mock Call
        mock_send.assert_called_once()


class WebhookTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.webhook_url = reverse('instagram_webhook')

    def test_webhook_verify_token(self):
        """Test GET request for webhook verification"""
        # We need to mock settings.INSTAGRAM_VERIFY_TOKEN if it's not set in test env
        with self.settings(INSTAGRAM_VERIFY_TOKEN='my_test_token'):
            response = self.client.get(self.webhook_url, {
                'hub.mode': 'subscribe',
                'hub.verify_token': 'my_test_token',
                'hub.challenge': '123456'
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.decode(), '123456')

    @patch('api.views.send_instagram_message')
    @patch('api.views.get_instagram_username')
    def test_webhook_receive_message(self, mock_get_user, mock_send):
        """Test POST request with incoming message"""
        mock_get_user.return_value = "webhook_tester"
        mock_send.return_value = True
        
        payload = {
            "object": "instagram",
            "entry": [{
                "changes": [{
                    "field": "messages",
                    "value": {
                        "sender": {"id": "999"},
                        "message": {"text": "Webhook works!"}
                    }
                }]
            }]
        }
        
        response = self.client.post(
            self.webhook_url,
            json.dumps(payload),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify Question Created
        q = Question.objects.get(instagram_user_id="999")
        self.assertEqual(q.question_text, "Webhook works!")
        self.assertEqual(q.instagram_username, "webhook_tester")
