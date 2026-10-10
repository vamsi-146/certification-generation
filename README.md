# Bulk Certificate Generator v2

A full-stack application for generating certificates in bulk with a FastAPI backend and Streamlit frontend.

## Features

- **Bulk Certificate Generation**: Submit a single request with up to 1000 recipients
- **Professional Certificate Design**: Elegant PDF certificates with double borders, corner ornaments, and QR codes
- **Real-time Progress Tracking**: Monitor generation status via API or frontend
- **Individual Failure Handling**: One certificate failure doesn't stop others
- **Batch Downloads**: Download all certificates as a ZIP file
- **Certificate Verification**: Verify certificate authenticity via unique ID

## Technology Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Frontend**: Streamlit
- **Certificate Generation**: ReportLab, QRCode
- **Testing**: Pytest

## Project Structure

```
.
├── backend/
│   └── app/
│       ├── main.py              # FastAPI application
│       ├── database.py          # Database configuration
│       ├── models.py            # SQLAlchemy models
│       ├── schemas.py           # Pydantic schemas
│       ├── routers/
│       │   ├── jobs.py          # Job endpoints
│       │   └── certificates.py  # Certificate endpoints
│       └── services/
│           └── certificate.py   # Certificate generation logic
├── frontend/
│   └── app.py                   # Streamlit frontend
├── tests/
│   └── test_api.py              # API tests
├── requirements.txt             # Python dependencies
├── sample_recipients.csv       # Sample input file
└── README.md                   # This file
```

## Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Navigate to backend directory**:
```bash
cd backend
```

## Running the Application

### Backend (FastAPI)

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Frontend (Streamlit)

In a new terminal:

```bash
cd frontend
streamlit run app.py
```

The frontend will be available at `http://localhost:8501`

## Running Tests

```bash
pytest tests/test_api.py -v
```

## API Endpoints

### Create Job
```bash
POST /api/jobs
Content-Type: application/json

{
  "event_name": "Python Workshop 2024",
  "issuer": "Tech Academy",
  "date": "October 9, 2024",
  "recipients": [
    {"name": "John Doe", "email": "john@example.com"},
    {"name": "Jane Smith", "email": "jane@example.com"}
  ]
}
```

Response: `202 Accepted` with job details

### Get Job Status
```bash
GET /api/jobs/{job_id}
```

Response: Job status with progress metrics

### Get Job Certificates
```bash
GET /api/jobs/{job_id}/certificates
```

Response: List of all certificates for the job

### Download Single Certificate
```bash
GET /api/certificates/{certificate_id}/download
```

Response: PDF file

### Download All Certificates (ZIP)
```bash
GET /api/jobs/{job_id}/download
```

Response: ZIP file containing all PDFs

### Verify Certificate
```bash
GET /api/certificates/verify/{certificate_id}
```

Response: Certificate validity and details

## Using the Frontend

1. Open `http://localhost:8501`
2. Configure API URL and event details in the sidebar
3. **Tab 1 - Generate Certificates**:
   - Upload a CSV/XLSX file with `name,email` columns
   - Or paste recipients manually (one per line: `name,email`)
   - Click "Generate Certificates"
4. **Tab 2 - Track Progress**:
   - Enter job ID (auto-filled from last job)
   - View progress bar and status
   - Download individual certificates or ZIP of all

## Example cURL Commands

```bash
# Create a job
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "Python Workshop",
    "issuer": "Tech Academy",
    "date": "2024-10-09",
    "recipients": [
      {"name": "John Doe", "email": "john@example.com"}
    ]
  }'

# Check job status
curl http://localhost:8000/api/jobs/1

# Download ZIP of certificates
curl http://localhost:8000/api/jobs/1/download --output certificates.zip

# Verify a certificate
curl http://localhost:8000/api/certificates/verify/{certificate_id}
```

## Design Decisions

### BackgroundTasks vs Celery

**Decision**: Used FastAPI's `BackgroundTasks` instead of Celery.

**Rationale**:
- **Simplicity**: BackgroundTasks is built into FastAPI, requiring no additional infrastructure (Redis, Celery worker)
- **Deployment**: Easier to deploy - single process vs multiple services
- **Use Case Fit**: For moderate workloads (up to 1000 certificates per job), BackgroundTasks is sufficient
- **Development**: Faster development and testing cycle

**Trade-offs**:
- BackgroundTasks run in the same process - if the server restarts, in-progress tasks are lost
- Celery would provide better durability and scaling for very high throughput
- For production at scale, Celery would be the better choice

### Per-Recipient Error Handling

Each certificate generation is wrapped in a try/except block. This ensures that:
- One invalid recipient doesn't prevent others from being processed
- Individual errors are captured and stored in the database
- The job status accurately reflects succeeded/failed counts

### Database Choice

**SQLite** was chosen for:
- Zero configuration - no separate database server needed
- Suitable for the expected workload
- Easy deployment and testing
- Can be upgraded to PostgreSQL if needed

### Certificate Design

The certificate uses:
- **ReportLab**: Reliable PDF generation library
- **Landscape A4**: Standard certificate format
- **Double border with ornaments**: Professional appearance
- **QR Code**: Links to verification endpoint for authenticity
- **Navy and gold color palette**: Professional, academic feel

## Future Enhancements

- Add email delivery of certificates
- Support multiple certificate templates
- Add certificate preview before generation
- Implement proper job queue with Celery for production scale
- Add authentication and authorization
- Support custom certificate designs via UI
