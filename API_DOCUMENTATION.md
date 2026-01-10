# Healthcare Q&A System - API Documentation

Base URL: `/` (e.g., `http://localhost:8000`)

## Authentication

### 1. Login
**Endpoint:** `POST /api/auth/login/`

**Description:** Authenticates a user and starts a session.

**Request Body:**
```json
{
  "username": "doctor_jane",
  "password": "secret_password"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "user": {
    "id": 1,
    "username": "doctor_jane",
    "full_name": "Jane Doe"
  }
}
```

**Response (401 Unauthorized):**
```json
{
  "error": "Invalid credentials"
}
```

---

### 2. Get Current User ("Me")
**Endpoint:** `GET /api/auth/me/`

**Description:** Returns details of the currently logged-in user. Requires session cookie.

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "doctor_jane",
  "full_name": "Jane Doe",
  "email": "jane@example.com",
  "is_staff": true
}
```

**Response (403 Forbidden):**
If user is not logged in.

---

### 3. Logout
**Endpoint:** `POST /api/auth/logout/`

**Description:** Logs out the user and destroys the session.

**Response (200 OK):**
```json
{
  "status": "logged_out"
}
```

---

## Questions & Answers

### 4. Get List of Questions
**Endpoint:** `GET /api/questions/`

**Query Parameters:**
- `status`: (Optional) Filter by status (`pending` or `answered`). Default returns all.

**Example Request:**
`GET /api/questions/?status=pending`

**Response (200 OK):**
```json
{
  "count": 5,
  "questions": [
    {
      "id": "a1b2c3d4-...",
      "instagram_username": "patient_zero",
      "question_text": "Does my headache mean I'm tired?",
      "status": "pending",
      "created_at": "2026-01-10T12:00:00Z",
      "answered_at": null,
      "answer_text": null,
      "answer_sent": false
    },
    ...
  ]
}
```

---

### 5. Get Question Detail
**Endpoint:** `GET /api/questions/<uuid:id>/`

**Description:** Get full details for a specific question.

**Response (200 OK):**
```json
{
  "id": "a1b2c3d4-...",
  "instagram_username": "patient_zero",
  "question_text": "Does my headache mean I'm tired?",
  "status": "answered",
  "created_at": "2026-01-10T12:00:00Z",
  "answered_at": "2026-01-10T14:30:00Z",
  "answer_text": "Yes, get some sleep.",
  "answer_sent": true,
  "answered_by": "doctor_jane"
}
```

---

### 6. Submit Answer
**Endpoint:** `POST /api/questions/<uuid:id>/answer/`

**Description:** Submits an answer to a question and automatically triggers an Instagram Direct Message to the user.

**Request Body:**
```json
{
  "answer": "This is the doctor's reply."
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Answer saved and sent to Instagram",
  "instagram_sent": true
}
```

**Response (400 Bad Request):**
```json
{
  "error": "Answer text is required"
}
```
