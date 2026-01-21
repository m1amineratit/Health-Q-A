# Question and Answer Models - Separation Documentation

## Overview

The **Question** and **Answer** models have been separated into distinct models with a **OneToOneField** relationship. Each question can have exactly one answer, and each answer is linked to exactly one question.

## Model Structure

### Question Model

```python
class Question(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('answered', 'Answered'),
        ('archived', 'Archived'),
    ]
    
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')
    category = models.CharField(max_length=150, blank=True, null=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instagram_username = models.CharField(max_length=100)
    instagram_user_id = models.CharField(max_length=100, blank=True)
    question_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    views_count = models.IntegerField(default=0)
```

**Fields:**
- `doctor`: Foreign key to User - the doctor who assigned the question
- `category`: Medical speciality (eyes, heart, generaliste, etc.)
- `id`: UUID primary key
- `instagram_username`: Username of the person asking the question
- `instagram_user_id`: Instagram user ID
- `question_text`: The actual question content
- `created_at`: When the question was created
- `status`: Current status (pending, answered, archived)
- `views_count`: Number of views for the question

**Related Names:**
- `answer`: Access the related Answer object
  ```python
  question.answer  # Returns the Answer object or None
  ```

### Answer Model

```python
class Answer(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name='answer')
    answered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='answers')
    answer_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    answer_sent = models.BooleanField(default=False)
    views_count = models.IntegerField(default=0)
```

**Fields:**
- `question`: OneToOne field to Question (one answer per question)
- `answered_by`: Foreign key to User - the doctor who answered
- `answer_text`: The actual answer content
- `created_at`: When the answer was created
- `updated_at`: Last time the answer was modified
- `answer_sent`: Whether the answer was sent to the user (via Instagram DM)
- `views_count`: Number of views for this answer

**Related Names:**
- `question.answer`: Access from the Question side

## Database Changes

A new migration file (`0007_separate_answer_model.py`) creates the Answer model and removes old fields from Question:

**Removed from Question:**
- `answered_by` (ForeignKey)
- `answered_at` (DateTime)
- `answer_text` (TextField)
- `answer_sent` (Boolean)

**New Answer Model** with all the above fields plus separate tracking.

## Accessing Data

### From Question to Answer
```python
question = Question.objects.get(id='some-uuid')

# Check if question has an answer
if hasattr(question, 'answer') and question.answer:
    answer = question.answer
    print(answer.answer_text)
    print(answer.answered_by.get_full_name())
    print(answer.created_at)
```

### From Answer to Question
```python
answer = Answer.objects.get(id=1)
print(answer.question.question_text)
print(answer.question.instagram_username)
```

### Filter Questions by Answer Status
```python
# Get all questions with answers
answered_questions = Question.objects.filter(status='answered')

# Get questions with answers that were sent
sent_questions = Question.objects.filter(answer__answer_sent=True)

# Get questions without answers
pending_questions = Question.objects.filter(answer__isnull=True)

# Get all answers by a specific doctor
doctor_answers = Answer.objects.filter(answered_by_id=user_id)
```

## API Endpoints

### Get Questions List
```
GET /api/questions/
```

**Response:**
```json
{
  "count": 5,
  "questions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "instagram_username": "user123",
      "question_text": "What should I do for headaches?",
      "category": "neurology",
      "status": "answered",
      "created_at": "2026-01-21T10:00:00Z",
      "answer": {
        "answer_text": "You should rest and...",
        "answered_by": "john_doe",
        "created_at": "2026-01-21T11:30:00Z",
        "answer_sent": true
      },
      "views_count": 45
    }
  ]
}
```

### Get Question Detail
```
GET /api/questions/{question_id}/
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "instagram_username": "user123",
  "question_text": "What should I do for headaches?",
  "status": "answered",
  "created_at": "2026-01-21T10:00:00Z",
  "answer": {
    "id": 1,
    "answer_text": "You should rest and take ibuprofen...",
    "answered_by": "john_doe",
    "answered_by_full_name": "Dr. John Doe",
    "created_at": "2026-01-21T11:30:00Z",
    "updated_at": "2026-01-21T11:45:00Z",
    "answer_sent": true,
    "views_count": 45
  },
  "views_count": 50
}
```

### Submit Answer
```
POST /api/questions/{question_id}/answer/
```

**Request Body:**
```json
{
  "answer": "You should rest and take ibuprofen. If symptoms persist..."
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Answer saved and sent to Instagram",
  "instagram_sent": true
}
```

### Get Answered Questions Feed
```
GET /api/questions/feed/answered/
```

Query Parameters:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 10, max: 100)

**Response:**
```json
{
  "status": "success",
  "count": 10,
  "total_count": 45,
  "page": 1,
  "limit": 10,
  "total_pages": 5,
  "has_next": true,
  "has_previous": false,
  "questions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "question_text": "What should I do for headaches?",
      "instagram_username": "user123",
      "category": "neurology",
      "answer_text": "You should rest and...",
      "answered_at": "2026-01-21T11:30:00Z",
      "created_at": "2026-01-21T10:00:00Z",
      "views_count": 50,
      "doctor": {
        "id": 1,
        "name": "Dr. John Doe",
        "speciality": "neurology",
        "speciality_display": "Neurologist",
        "phone": "+212612345678",
        "img": "http://example.com/img.jpg"
      }
    }
  ]
}
```

## Serializers

### QuestionSerializer
Used for list views. Includes related Answer data.

```python
from api.serializers import QuestionSerializer

serializer = QuestionSerializer(question)
print(serializer.data)
```

### QuestionDetailSerializer
Used for detail views. Includes full Answer information.

### AnswerSerializer
For answer-specific operations.

```python
from api.serializers import AnswerSerializer

serializer = AnswerSerializer(answer)
print(serializer.data)
```

### CreateAnswerSerializer
For creating new answers.

```python
serializer = CreateAnswerSerializer(data={
    'question': question_id,
    'answer_text': 'The answer...',
    'answer_sent': False
})
```

## Benefits of Separation

1. **Single Responsibility**: Each model has a clear purpose
2. **Better Data Organization**: Answer data is separate and organized
3. **Independent Queries**: Can query answers without loading questions
4. **Flexible Updates**: Can update answers independently
5. **Clear Relationships**: OneToOne relationship is explicit
6. **Answer Tracking**: Separate timestamps and sent status
7. **Scalability**: Easier to extend each model independently

## Migration Steps

1. Run the migration:
   ```bash
   python manage.py migrate api
   ```

2. The migration will:
   - Create the new Answer model
   - Copy data from Question to Answer (if you have existing data)
   - Remove old fields from Question

## Handling Existing Data

If you have existing questions with answers, you'll need a data migration:

```python
def migrate_answers(apps, schema_editor):
    Question = apps.get_model('api', 'Question')
    Answer = apps.get_model('api', 'Answer')
    
    for question in Question.objects.filter(answer_text__isnull=False):
        if not hasattr(question, 'answer'):
            Answer.objects.create(
                question=question,
                answer_text=question.answer_text,
                answered_by_id=question.answered_by_id,
                answer_sent=question.answer_sent
            )
```

## Common Patterns

### Check if Question Has Answer
```python
if hasattr(question, 'answer') and question.answer:
    # Process answer
    pass
```

### Get Answer with Related Doctor Info
```python
answer = Answer.objects.select_related(
    'answered_by',
    'answered_by__doctor_profile'
).get(id=answer_id)

doctor = answer.answered_by.doctor_profile
```

### Create Answer with Related Data
```python
from django.utils import timezone

answer = Answer.objects.create(
    question=question,
    answered_by=request.user,
    answer_text="The answer text...",
    answer_sent=True
)

# Update question status
question.status = 'answered'
question.save()
```

## Testing

### Test Creating Answer
```python
from django.test import TestCase
from api.models import Question, Answer
from django.contrib.auth.models import User

class AnswerModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', 'test@example.com', 'pass')
        self.question = Question.objects.create(
            doctor=self.user,
            instagram_username='user123',
            question_text='Test question',
            category='neurology'
        )
    
    def test_create_answer(self):
        answer = Answer.objects.create(
            question=self.question,
            answered_by=self.user,
            answer_text='Test answer'
        )
        
        self.assertEqual(self.question.answer, answer)
        self.assertEqual(answer.question, self.question)
```

## Admin Panel

The Answer model will appear in Django admin. You can:
- View all answers
- Filter by answered_by, answer_sent status
- Search by answer_text
- View related question details

To enable in admin, add to `admin.py`:

```python
from django.contrib import admin
from .models import Answer

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['id', 'question', 'answered_by', 'answer_sent', 'created_at']
    list_filter = ['answer_sent', 'created_at', 'answered_by']
    search_fields = ['answer_text', 'question__question_text']
    readonly_fields = ['created_at', 'updated_at']
```

## Troubleshooting

### Answer not appearing in queryset
Make sure to use `select_related('answer')`:
```python
questions = Question.objects.select_related('answer')
```

### IntegrityError on answer creation
Ensure the question exists and hasn't already been answered:
```python
if hasattr(question, 'answer') and question.answer:
    raise Exception("Question already has an answer")
```

### Querying old fields
If you're still using old field names, update them:
```python
# OLD (won't work)
question.answer_text

# NEW
question.answer.answer_text if question.answer else None
question.answered_by

# NEW  
question.answer.answered_by if question.answer else None
```
