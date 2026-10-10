from fastapi import APIRouter, Response
from typing import List
import uuid
import zipfile
import os
from io import BytesIO
from ..schemas import JobCreate
from ..services.certificate import generate_certificate

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

CERT_DIR = "certificates"

@router.post("", status_code=200)
def create_job(job: JobCreate):
    # Generate certificates synchronously
    certificate_files = []
    
    for recipient in job.recipients:
        certificate_id = str(uuid.uuid4())
        try:
            filepath = generate_certificate(
                certificate_id,
                recipient.name,
                job.event_name,
                job.issuer,
                job.date
            )
            certificate_files.append({
                "certificate_id": certificate_id,
                "name": recipient.name,
                "email": recipient.email,
                "file_path": filepath
            })
        except Exception as e:
            certificate_files.append({
                "certificate_id": certificate_id,
                "name": recipient.name,
                "email": recipient.email,
                "error": str(e)
            })
    
    return {
        "event_name": job.event_name,
        "issuer": job.issuer,
        "date": job.date,
        "certificates": certificate_files
    }

@router.post("/download")
def download_certificates(certificates: List[dict]):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for cert in certificates:
            if 'file_path' in cert and os.path.exists(cert['file_path']):
                zipf.write(cert['file_path'], f"{cert['name']}.pdf")
    
    zip_buffer.seek(0)
    
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=certificates.zip"}
    )
