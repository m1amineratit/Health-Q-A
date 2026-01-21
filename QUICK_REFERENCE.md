# Quick Reference - Question & Answer Separation

## Model Relationship

```
Question (1) ←→ (1) Answer
```

## Database Schema

### Question Table
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary Key |
| doctor_id | Int FK | Who assigned the question |
| category | Str | Medical speciality |
| instagram_username | Str | Questioner's Instagram handle |
| instagram_user_id | Str | Instagram user ID |
| question_text | Text | The question content |
| created_at | DateTime | When asked |
| status | Str | pending/answered/archived |
| views_count | Int | Question views |

### Answer Table
| Column | Type | Notes |
|--------|------|-------|
| id | Int | Primary Key |
| question_id | UUID FK | OneToOne to Question |
| answered_by_id | Int FK | Doctor who answered |
| answer_text | Text | The answer content |
| created_at | DateTime | When answered |
| updated_at | DateTime | Last modified |
| answer_sent | Bool | DM sent to user? |
| views_count | Int | Answer views |

## API Response Examples

### Question with Answer
```json
{
  "id": "uuid-here",
  "question_text": "How to treat headache?",
  "instagram_username": "user123",
  "category": "neurology",
  "status": "answered",
  "created_at": "2026-01-21T10:00:00Z",
  "answer": {
    "answer_text": "Rest and take medicine...",
    "answered_by": "john_doe",
    "created_at": "2026-01-21T11:30:00Z",
    "answer_sent": true
  },
  "views_count": 50
}
```

### Question without Answer
```json
{
  "id": "uuid-here",
  "question_text": "How to treat headache?",
  "instagram_username": "user123",
  "category": "neurology",
  "status": "pending",
  "created_at": "2026-01-21T10:00:00Z",
  "answer": null,
  "views_count": 5
}
```

## Python Examples

### Accessing Answer from Question
```python
question = Question.objects.get(id='...')

# Check if answer exists
if question.answer:
    print(question.answer.answer_text)
    print(question.answer.answered_by.username)
```

### Creating an Answer
```python
Answer.objects.create(
    question=question_obj,
    answered_by=user_obj,
    answer_text="The answer here...",
    answer_sent=False
)
```

### Querying
```python
# Questions with answers
answered = Question.objects.filter(status='answered')

# Answers sent to users
sent = Answer.objects.filter(answer_sent=True)

# Answers by doctor
doctor_answers = Answer.objects.filter(answered_by_id=doc_id)
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/questions/` | GET | List all questions |
| `/api/questions/{id}/` | GET | Question details |
| `/api/questions/{id}/answer/` | POST | Submit answer |
| `/api/questions/feed/answered/` | GET | Answered questions feed |

## Frontend Integration

### Handling Answer in Response
```javascript
// Old (won't work)
response.answer_text

// New (correct)
response.answer?.answer_text

// Check if answered
if (response.answer) {
  console.log('Has answer:', response.answer.answer_text);
}
```

### Submitting Answer
```javascript
POST /api/questions/{id}/answer/
Body: { "answer": "Your answer text..." }
```

## Admin Commands

```bash
# Run migrations
python manage.py migrate api

# Create answer in shell
from api.models import Question, Answer
q = Question.objects.first()
a = Answer.objects.create(
    question=q,
    answered_by=user,
    answer_text="..."
)

# Check relationships
q.answer  # Returns Answer or None
a.question  # Returns Question
```

## Common Tasks

### Check if question is answered
```python
if hasattr(question, 'answer') and question.answer:
    # Yes, it has an answer
```

### Get question status
```python
if question.status == 'answered' and question.answer:
    # Has answer and marked as answered
```

### Update answer
```python
answer = question.answer
answer.answer_text = "Updated answer..."
answer.save()
```

### Delete answer
```python
question.answer.delete()  # Deletes answer only
question.status = 'pending'
question.save()
```

## Migration Command

```bash
python manage.py migrate api 0007_separate_answer_model
```

## Files Changed

1. `api/models.py` - Models updated
2. `api/serializers.py` - New serializers added
3. `api/json_api.py` - Endpoints updated
4. `api/migrations/0007_separate_answer_model.py` - Database migration

## Troubleshooting

**"Answer not found"**
```python
if question.answer is None:
    print("No answer yet")
```

**"Can't update answer_text on Question"**
```python
# Use answer object
question.answer.answer_text = "..."
question.answer.save()
```

**"Multiple answers error"**
```python
# Only one answer per question (OneToOne)
# Delete first answer before creating new one
question.answer.delete()
```

## Performance Tips

1. Use `select_related('answer')` when fetching questions:
   ```python
   Question.objects.select_related('answer')
   ```

2. Use `select_related` when fetching answers:
   ```python
   Answer.objects.select_related('question', 'answered_by')
   ```

---

**For detailed documentation, see:**
- `QUESTION_ANSWER_SEPARATION.md` - Complete guide
- `IMPLEMENTATION_SUMMARY.md` - Summary of changes
