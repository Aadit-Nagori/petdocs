import base64
from datetime import datetime
from io import BytesIO
from typing import BinaryIO

import qrcode
from django.utils import timezone

from .models import Document, Pet, Sharelink

MIME_TYPES = ["image/jpeg", "image/png", "application/pdf"]
def upload_document(pet: Pet, file: BinaryIO, name: str, file_type: str) -> Document:
    
    #validate file
    if file.content_type not in MIME_TYPES:
        raise TypeError("File type not accepted")
    elif file.size > 3 * 1024 * 1024:                       #3MB
        raise MemoryError("File size too large")
    
    #try uploading to Supabase S3
    try:
        document = Document(pet=pet,name=name,file_type=file_type)
        document.file.save(file.name,file,save=False)
    except ConnectionError as exc:
        raise RuntimeError('Failed to save file to S3') from exc
    
    #try uploading to DB - if fails rollback S3 uploaded file
    try:
        document.save()
    except Exception as exc:
        document.file.delete(save=False)
        raise RuntimeError('Failed to save Document Record to DB') from exc

    return document

def delete_document(pet: Pet, document: Document) -> bool:
    #validate permissions
    if document.pet != pet:
        raise PermissionError("Document does not belong to this pet")
    
    try:
        document.file.delete(save=False)
    except Exception as exc:
        raise RuntimeError('Failed to delete document from S3') from exc
    
    try:
        document.delete()
    except Exception as exc:
        raise RuntimeError("Failed to delete document record from DB") from exc
    
    return True

def create_sharelink(pet: Pet, document_ids: list[int], expires_at: datetime) -> Sharelink:  # noqa: E501
    documents = Document.objects.filter(pk__in=document_ids,pet=pet)
    if len(documents) != len(document_ids):
        raise ValueError("incorrect number of documents requested")
    if expires_at < timezone.now():
        raise ValueError("sharelink expires before creation")
    sharelink = Sharelink(pet=pet,expires_at=expires_at)
    sharelink.save()
    sharelink.documents.set(documents)
    return sharelink

def generate_qrcode(url: str) -> str:
    buffer = BytesIO()
    qr_image = qrcode.make(url)
    qr_image.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()

def validate_sharelink(token: str) -> Sharelink:
    try:
        sharelink = Sharelink.objects.get(token=token)
    except Sharelink.DoesNotExist as exc:
        raise ValueError("Sharelink does not exist") from exc
    if not sharelink.is_active or sharelink.is_expired:
        raise PermissionError("sharelink expired")
    return sharelink

def deactivate_sharelink(pet: Pet, sharelink: Sharelink) -> bool:
    if sharelink.pet != pet:
        raise PermissionError("Sharelink does not belong to this pet")
    sharelink.is_active = False
    sharelink.save()
    return True
    