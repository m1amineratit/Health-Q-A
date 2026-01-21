# Architecture Diagrams - Question & Answer Separation

## 1. Database Schema Diagram

```
┌─────────────────────────────────────┐
│         Question Table              │
├─────────────────────────────────────┤
│ PK: id (UUID)                       │
│ FK: doctor_id → User                │
│ category (CharField)                │
│ instagram_username                  │
│ instagram_user_id                   │
│ question_text                       │
│ created_at                          │
│ status (pending|answered|archived)  │
│ views_count                         │
└─────────────────────────────────────┘
           │
           │ OneToOne Relationship
           │ related_name='answer'
           │
           ▼
┌─────────────────────────────────────┐
│         Answer Table                │
├─────────────────────────────────────┤
│ PK: id                              │
│ FK: question_id → Question (1:1)    │
│ FK: answered_by_id → User           │
│ answer_text                         │
│ created_at                          │
│ updated_at                          │
│ answer_sent (Boolean)               │
│ views_count                         │
└─────────────────────────────────────┘
```

## 2. Object Relationship Diagram

```
User (Doctor)
    │
    ├─→ Many Questions (doctor_id FK)
    │   └─→ One Answer (OneToOne)
    │       └─→ User (answered_by FK)
    │
    └─→ Many Answers (answered_by_id FK)
```

## 3. API Request/Response Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    API CLIENT (Frontend)                     │
└────────────────────┬─────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
    GET /api/    POST /api/    GET /api/
    questions/  questions/    questions/
              {id}/answer/    feed/answered/
        │            │            │
        └────────────┼────────────┘
                     │
        ┌────────────▼──────────────┐
        │   API Endpoints Layer     │
        │ (json_api.py)             │
        └────────────┬──────────────┘
                     │
        ┌────────────▼──────────────┐
        │  Serializer Layer         │
        │  (serializers.py)         │
        │ - QuestionSerializer      │
        │ - AnswerSerializer        │
        └────────────┬──────────────┘
                     │
        ┌────────────▼──────────────┐
        │   Model Layer             │
        │  (models.py)              │
        │ - Question ←→ Answer      │
        └────────────┬──────────────┘
                     │
        ┌────────────▼──────────────┐
        │   Database Layer          │
        │  - Question table         │
        │  - Answer table           │
        └──────────────────────────┘
```

## 4. Question Lifecycle

```
Step 1: Create Question
┌─────────────────────────────────────┐
│ User submits question via Instagram │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Question Created                    │
│ status = 'pending'                  │
│ answer = None                       │
└────────────┬────────────────────────┘
             │
             │ Doctor browses pending
             │
             ▼
Step 2: Answer Question
┌─────────────────────────────────────┐
│ Doctor Submits Answer               │
│ POST /api/questions/{id}/answer/    │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Answer Created                      │
│ - Linked to Question (OneToOne)    │
│ - question.answer now exists        │
│ - answer.created_at set             │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Question Updated                    │
│ status = 'answered'                 │
│ answer object now linked            │
└────────────┬────────────────────────┘
             │
             ▼
Step 3: Send Answer
┌─────────────────────────────────────┐
│ Instagram DM Sent to User           │
│ answer.answer_sent = True           │
└────────────┬────────────────────────┘
             │
             ▼
Step 4: Public Feed
┌─────────────────────────────────────┐
│ Question appears in public feed     │
│ status = 'answered'                 │
│ answer.answer_sent = True           │
│ Views tracked separately            │
└─────────────────────────────────────┘
```

## 5. Data Access Patterns

```
PATTERN 1: Get Question with Answer
─────────────────────────────────────
Question.objects
  .select_related('answer')
  .get(id='...')
       │
       ├─ question.question_text
       ├─ question.status
       └─ question.answer
          ├─ answer.answer_text
          ├─ answer.answered_by
          └─ answer.answer_sent


PATTERN 2: Get All Answered Questions
──────────────────────────────────────
Question.objects
  .filter(status='answered')
  .select_related('answer', 'answer__answered_by')
  .filter(answer__answer_sent=True)
       │
       ├─ question[0].answer.answer_text
       ├─ question[0].answer.answered_by.name
       └─ question[0].answer.views_count


PATTERN 3: Get Answers by Doctor
─────────────────────────────────
Answer.objects
  .filter(answered_by_id=doctor_id)
  .select_related('question', 'answered_by')
       │
       ├─ answer[0].question.question_text
       ├─ answer[0].answer_text
       └─ answer[0].created_at
```

## 6. API Response Structure

```
GET /api/questions/
───────────────────

Response: {
  "count": 2,
  "questions": [
    {
      "id": "uuid-1",
      "question_text": "How to treat X?",
      "status": "answered",
      "created_at": "2026-01-21T10:00:00Z",
      
      "answer": {                          ← Nested Answer
        "answer_text": "Treatment is...",
        "answered_by": "doctor_name",
        "created_at": "2026-01-21T11:00:00Z",
        "answer_sent": true
      },
      
      "views_count": 50
    },
    {
      "id": "uuid-2",
      "question_text": "How to treat Y?",
      "status": "pending",
      "created_at": "2026-01-21T09:00:00Z",
      
      "answer": null,                      ← No Answer Yet
      
      "views_count": 5
    }
  ]
}
```

## 7. Migration Process Flow

```
┌──────────────────────────────────────┐
│  Before Migration                    │
│  ─────────────────────────────────── │
│  Question Table:                     │
│  ├─ question_text                   │
│  ├─ answered_by (FK)                │
│  ├─ answered_at (DateTime)          │
│  ├─ answer_text                     │
│  └─ answer_sent                     │
└────────────┬─────────────────────────┘
             │
    python manage.py migrate api
             │
             ▼
┌──────────────────────────────────────┐
│  Migration Operations:               │
│  ─────────────────────────────────── │
│  1. Create Answer table              │
│  2. Create OneToOne relationship    │
│  3. Drop answer_* fields from Q    │
│  4. Update status                   │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  After Migration                     │
│  ─────────────────────────────────── │
│  Question Table:                     │
│  ├─ question_text                   │
│  ├─ status                          │
│  └─ [id FK] → Answer                │
│                                      │
│  Answer Table (NEW):                │
│  ├─ question (OneToOne FK)         │
│  ├─ answered_by (FK)               │
│  ├─ answer_text                    │
│  ├─ answer_sent                    │
│  ├─ created_at                     │
│  └─ updated_at                     │
└──────────────────────────────────────┘
```

## 8. Function Call Flow - Submit Answer

```
POST /api/questions/{id}/answer/
          │
          ▼
┌─────────────────────────────────┐
│ submit_answer_api()             │
├─────────────────────────────────┤
│ 1. Get answer_text from request │
│ 2. Get Question object          │
│ 3. Check no answer exists       │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ Answer.objects.create()         │
├─────────────────────────────────┤
│ - question = question_obj       │
│ - answered_by = request.user    │
│ - answer_text = answer_text     │
│ - answer_sent = False (default) │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ Update Question Status          │
├─────────────────────────────────┤
│ question.status = 'answered'    │
│ question.save()                 │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ Send Instagram DM               │
├─────────────────────────────────┤
│ send_instagram_message()        │
│ success = True/False            │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ Update Answer Sent Status       │
├─────────────────────────────────┤
│ answer.answer_sent = success    │
│ answer.save()                   │
└────────────┬────────────────────┘
             │
             ▼
Return Response: {
  "status": "success",
  "instagram_sent": true/false
}
```

## 9. Comparison: Before vs After

```
BEFORE (Single Model)
──────────────────────────────────────
Question
├─ question_text ────────┐
├─ answered_by           │ Answer fields
├─ answered_at           │ mixed in
├─ answer_text ──────────┤
├─ answer_sent           │
└─ views_count ──────────┘

Problem: Multiple concerns in one model


AFTER (Separated Models)
──────────────────────────────────────
Question                 Answer
├─ question_text         ├─ question (FK)
├─ status                ├─ answer_text
└─ views_count           ├─ answered_by (FK)
                         ├─ answer_sent
                         ├─ created_at
                         ├─ updated_at
                         └─ views_count

Benefit: Clear separation of concerns
```

## 10. ORM Query Examples

```python
# Get question with answer
q = Question.objects.select_related('answer').get(id='...')
answer_text = q.answer.answer_text if q.answer else None

# Get all answered questions
answered = Question.objects.filter(
    answer__answer_sent=True
).select_related('answer', 'answer__answered_by')

# Get answers by doctor
doctor_answers = Answer.objects.filter(
    answered_by_id=doc_id
).select_related('question')

# Count answers per doctor
from django.db.models import Count
Answer.objects.values('answered_by__username').annotate(
    count=Count('id')
)
```

---

**Diagrams Created:** 10
**Key Concepts Illustrated:** ORM, API, Database, Lifecycle, Patterns
**Use Case:** Understanding the Question-Answer separation architecture
