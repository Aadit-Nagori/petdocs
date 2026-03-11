from typing import BinaryIO

from .models import Document, Pet

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
        raise RuntimeError('Failed to save file to Supabase') from exc
    
    #try uploading to DB - if fails rollback S3 uploaded file
    try:
        document.save()
    except Exception as exc:
        document.file.delete(save=False)
        raise RuntimeError('Failed to save Document Record to DB') from exc

    return document

    
    
    