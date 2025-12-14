# SEOgen API - Phase 2

A minimal FastAPI application for license validation and page generation.

**Requirements: Python 3.11+**

## Tech Stack

- **FastAPI** - Modern Python web framework
- **Pydantic v2** - Data validation and serialization
- **Supabase** - Database and backend services
- **Python 3.11** - Runtime environment

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app and endpoints
│   ├── config.py         # Environment variable management
│   ├── supabase_client.py # Database client and operations
│   └── models.py         # Pydantic request/response models
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variable template
└── README.md           # This file
```

## Setup Instructions

### 1. Clone and Navigate
```bash
cd /path/to/seogen
```

### 2. Create Virtual Environment
**Important: This project requires Python 3.11+**

```bash
# Verify Python 3.11 is installed
python3.11 --version

# Create virtual environment with Python 3.11
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your Supabase credentials
# SUPABASE_URL=your_supabase_project_url_here
# SUPABASE_SECRET_KEY=your_supabase_secret_key_here
```

### 5. Database Schema
Ensure your Supabase database has the `licenses` table:

```sql
CREATE TABLE licenses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    license_key TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL,
    credits_remaining INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 6. Run the Application
```bash
uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`

## API Endpoints

### Health Check
```
GET /health
```

Response:
```json
{
  "status": "ok"
}
```

### Generate Page
```
POST /generate-page
```

Request:
```json
{
  "license_key": "your-license-key"
}
```

Response (Success):
```json
{
  "title": "Test Roofing Service Page",
  "blocks": [
    {
      "type": "heading",
      "text": "Roof Repair in Dallas, TX"
    },
    {
      "type": "paragraph", 
      "text": "This is placeholder content for Phase 2."
    }
  ]
}
```

Error Responses:
- `403` - License not found or inactive
- `402` - No credits remaining

## Interactive API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Railway Deployment

This project is ready for Railway deployment. The application will automatically use environment variables set in Railway's dashboard.

## Development Notes

- No authentication systems implemented (as per Phase 2 constraints)
- No Stripe integration
- No background jobs or async queues
- No AI calls
- Minimal and readable codebase
- Clear function boundaries and centralized database client
