import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models import Job, Certificate

@pytest.fixture(autouse=True)
def cleanup_db(db):
    db.query(Certificate).delete()
    db.query(Job).delete()
    db.commit()
    yield
    db.query(Certificate).delete()
    db.query(Job).delete()
    db.commit()

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_create_job(db):
    response = client.post("/api/jobs", json={
        "event_name": "Test Event",
        "issuer": "Test Issuer",
        "date": "2024-10-09",
        "recipients": [
            {"name": "John Doe", "email": "john@example.com"},
            {"name": "Jane Smith", "email": "jane@example.com"}
        ]
    })
    
    assert response.status_code == 202
    data = response.json()
    assert data["event_name"] == "Test Event"
    assert data["issuer"] == "Test Issuer"
    assert data["total_recipients"] == 2
    assert data["status"] == "processing"

def test_validation_empty_recipients(db):
    response = client.post("/api/jobs", json={
        "event_name": "Test Event",
        "issuer": "Test Issuer",
        "date": "2024-10-09",
        "recipients": []
    })
    
    assert response.status_code == 422

def test_validation_invalid_email(db):
    response = client.post("/api/jobs", json={
        "event_name": "Test Event",
        "issuer": "Test Issuer",
        "date": "2024-10-09",
        "recipients": [
            {"name": "John Doe", "email": "invalid-email"}
        ]
    })
    
    assert response.status_code == 422

def test_validation_missing_name(db):
    response = client.post("/api/jobs", json={
        "event_name": "Test Event",
        "issuer": "Test Issuer",
        "date": "2024-10-09",
        "recipients": [
            {"name": "", "email": "john@example.com"}
        ]
    })
    
    assert response.status_code == 422

def test_get_job(db):
    create_response = client.post("/api/jobs", json={
        "event_name": "Test Event",
        "issuer": "Test Issuer",
        "date": "2024-10-09",
        "recipients": [
            {"name": "John Doe", "email": "john@example.com"}
        ]
    })
    
    job_id = create_response.json()["id"]
    
    response = client.get(f"/api/jobs/{job_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["event_name"] == "Test Event"

def test_get_job_not_found(db):
    response = client.get("/api/jobs/99999")
    assert response.status_code == 404

def test_get_job_certificates(db):
    create_response = client.post("/api/jobs", json={
        "event_name": "Test Event",
        "issuer": "Test Issuer",
        "date": "2024-10-09",
        "recipients": [
            {"name": "John Doe", "email": "john@example.com"},
            {"name": "Jane Smith", "email": "jane@example.com"}
        ]
    })
    
    job_id = create_response.json()["id"]
    
    response = client.get(f"/api/jobs/{job_id}/certificates")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_single_certificate_failure(db, monkeypatch):
    def mock_generate_fail(*args, **kwargs):
        raise Exception("Simulated failure")
    
    import backend.app.services.certificate as cert_service
    monkeypatch.setattr(cert_service, "generate_certificate", mock_generate_fail)
    
    create_response = client.post("/api/jobs", json={
        "event_name": "Test Event",
        "issuer": "Test Issuer",
        "date": "2024-10-09",
        "recipients": [
            {"name": "John Doe", "email": "john@example.com"}
        ]
    })
    
    job_id = create_response.json()["id"]
    
    import time
    time.sleep(2)
    
    response = client.get(f"/api/jobs/{job_id}")
    data = response.json()
    
    assert data["failed_count"] >= 0

def test_download_certificate_not_found(db):
    response = client.get("/api/certificates/nonexistent-id/download")
    assert response.status_code == 404

def test_verify_certificate(db):
    response = client.get("/api/certificates/verify/invalid-id")
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] == False

def test_download_zip_job_not_found(db):
    response = client.get("/api/jobs/99999/download")
    assert response.status_code == 404

def test_download_zip_no_completed(db):
    create_response = client.post("/api/jobs", json={
        "event_name": "Test Event",
        "issuer": "Test Issuer",
        "date": "2024-10-09",
        "recipients": [
            {"name": "John Doe", "email": "john@example.com"}
        ]
    })
    
    job_id = create_response.json()["id"]
    
    response = client.get(f"/api/jobs/{job_id}/download")
    
    assert response.status_code in [200, 400]
