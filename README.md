# Bulk Certificate Generator

Generate PDF certificates for many recipients in a single request. FastAPI backend, Streamlit frontend.

## Features

- **Bulk generation**: one request with up to 1000 recipients
- **Input validation**: event name, issuer, date and recipient name are required; emails must be valid (Pydantic)
- **Per-recipient failure handling**: if one certificate fails to generate, the others still complete
- **Certificate design**: landscape A4 PDF, navy and gold, triple border, corner ornaments; long names and event titles shrink automatically to fit
- **Downloads**: individual PDFs or all successful certificates as one ZIP
- **Streamlit UI**: CSV upload or manual paste, with a popup if event details are missing

## Tech Stack

- **Backend**: FastAPI, Pydantic, ReportLab
- **Frontend**: Streamlit, httpx, pandas
- **Testing**: pytest

## Project Structure

```
.
├── backend/
│   └── app/
│       ├── main.py               # FastAPI app, CORS, router registration
│       ├── routers/jobs.py       # Generate and ZIP endpoints
│       ├── services/certificate.py  # PDF generation (ReportLab)
│       ├── schemas.py            # Request validation (Pydantic)
│       ├── models.py             # SQLAlchemy models (not used in the current flow)
│       └── database.py           # SQLite setup (not used in the current flow)
├── frontend/
│   ├── app.py                    # Streamlit UI
│   └── .streamlit/config.toml    # Light theme
├── tests/test_api.py
├── requirements.txt
├── sample_recipients.csv
├── assignment.md
└── README.md
```

Generated PDFs are saved to `backend/certificates/` at runtime.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running

Start the backend (run it from the `backend` folder, because certificates are saved relative to the working directory):

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`

In a second terminal, start the frontend:

```bash
cd frontend
streamlit run app.py
```

The UI opens at `http://localhost:8501` (Streamlit uses the next free port if that one is busy).

Run both on the same machine. The frontend reads the PDFs directly from `../backend/certificates/` for the individual download buttons.

## Using the Frontend

1. In the sidebar, enter **Event Name**, **Issuer** and **Date**. They start empty and are all required; a popup lists any that are missing when you click Generate.
2. Add recipients:
   - **Upload CSV**: columns `name,email`, **no header row**
   - **Paste Manually**: one `name,email` per line
3. Click **Generate Certificates**.
4. The results show the successful and failed counts, with an error for each failure.
5. Click **Download All (ZIP)**, then **Download ZIP**, or use the per-person buttons for individual PDFs.

## API

### POST `/api/jobs`

Generates a certificate for every recipient and returns the results. Status `200`.

Request:

```json
{
  "event_name": "Python Workshop 2026",
  "issuer": "Tech Academy",
  "date": "October 10, 2026",
  "recipients": [
    {"name": "John Doe", "email": "john@example.com"},
    {"name": "Jane Smith", "email": "jane@example.com"}
  ]
}
```

Response:

```json
{
  "event_name": "Python Workshop 2026",
  "issuer": "Tech Academy",
  "date": "October 10, 2026",
  "certificates": [
    {"certificate_id": "uuid", "name": "John Doe", "email": "john@example.com", "file_path": "certificates/<uuid>.pdf"},
    {"certificate_id": "uuid", "name": "Jane Smith", "email": "jane@example.com", "error": "reason it failed"}
  ]
}
```

Each entry has either `file_path` (success) or `error` (failure).

**Validation (422):** empty event name, issuer or date; empty recipients list or more than 1000; empty name; invalid email. A validation error rejects the whole request.

### POST `/api/jobs/download`

Takes the `certificates` array from the previous response and returns `certificates.zip` containing one `<name>.pdf` per entry that has a `file_path`.

### GET `/`

Health message.

### Example cURL

```bash
# Generate certificates
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "Python Workshop",
    "issuer": "Tech Academy",
    "date": "October 10, 2026",
    "recipients": [{"name": "John Doe", "email": "john@example.com"}]
  }'

# Download a ZIP (use a file_path from the response above)
curl -X POST http://localhost:8000/api/jobs/download \
  -H "Content-Type: application/json" \
  -d '[{"name": "John Doe", "file_path": "certificates/<uuid>.pdf"}]' \
  --output certificates.zip
```

## Design Decisions

**Synchronous generation.** The API generates all certificates during the request and returns the result immediately. This is simple, needs no polling or queue, and is fine for up to a few hundred certificates. The trade-off is that the request blocks until finished (the frontend waits up to 120 seconds). For larger volumes, move generation to a background worker (FastAPI BackgroundTasks, or Celery with Redis for durability) and persist job status.

**Per-recipient error handling.** Each certificate is generated inside its own try/except, so one failure is recorded with its error and the rest continue.

**Validation at the API boundary.** Pydantic rejects bad input before any generation starts, which keeps the generation loop simple.

**Stateless flow.** Results come back in the response and PDFs live on disk. The SQLAlchemy models exist but are not wired in yet.

**Simple certificate layout.** All positions are computed from the page size, and text is shrunk to fit so long names never overflow or overlap.

## Known Limitations

- No persistent job tracking: there are no job IDs, status or progress endpoints
- No endpoints to retrieve a job or a single certificate later by ID
- One invalid email rejects the entire request instead of only that recipient
- The ZIP endpoint trusts `file_path` values sent by the client; it should look files up by certificate ID instead
- Individual downloads in the UI work only when the frontend and backend run on the same machine
- `tests/test_api.py` was written for an earlier database-backed design and does not match the current endpoints

## Future Enhancements

- Persist jobs and certificates in the database with status tracking (pending, processing, completed)
- Process jobs in the background and add job status, certificate list and per-certificate download endpoints
- Validate recipients individually so bad rows fail alone
- Email delivery of certificates
- Multiple certificate templates
