# Instagram Healthcare Q&A Backend

This is the Django backend for the Instagram Healthcare Q&A system. It handles Instagram webhooks, manages questions/answers, and provides a JSON API for the frontend dashboard.

## 📋 Prerequisites

- Python 3.10 or higher
- `pip` (Python package manager)
- A Meta Developer App (for Instagram Graph API credentials)

## 🛠️ Setup Instructions

### 1. Clone & Navigate
Navigate to the project directory:
```bash
cd backend/system
```

### 2. Create Virtual Environment
It is recommended to use a virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies
Install all required Python packages:
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the `system` folder (same level as `manage.py`) and add your credentials:

```ini
# Security
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,.ngrok-free.app

# Instagram Graph API
PAGE_ID=17841474626204259
INSTAGRAM_ACCESS_TOKEN=your_long_lived_page_token
INSTAGRAM_VERIFY_TOKEN=your_custom_verify_token
CLIENT_ID=your_app_client_id
CLIENT_SECRET=your_app_client_secret

# AI (Optional)
OPENROUTER_API_KEY=your_key_here
```

### 5. Run the Server
Start the development server:
```bash
python manage.py runserver
```
The server will start at `http://127.0.0.1:8000/`.

---

## 📚 API Documentation (For Frontend Developers)

The backend provides a fully documented JSON API.

### Interactive Documentation (Swagger UI)
Once the server is running, visit:
👉 **[http://localhost:8000/swagger/](http://localhost:8000/swagger/)**

This UI allows you to explore all endpoints, see request/response schemas, and even test requests directly from the browser.

### Key Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| **POST** | `/api/auth/login/` | Login and start session |
| **GET** | `/api/auth/me/` | Get current user details |
| **GET** | `/api/questions/` | List all questions (filter `?status=pending`) |
| **GET** | `/api/questions/{id}/` | Get details of one question |
| **POST** | `/api/questions/{id}/answer/` | Submit answer & Send DM to Patient |

### Alternative Docs
- **ReDoc:** `http://localhost:8000/redoc/`
- **Markdown File:** See `API_DOCUMENTATION.md` in the project root for a static reference.

## 🧪 Testing

To run the automated test suite:
```bash
python manage.py test api
```
