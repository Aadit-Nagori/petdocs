from datetime import timedelta
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.fields.files import FieldFile
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import Account

from .models import Document, Pet, Sharelink
from .services import (
    SharelinkExpiredError,
    SharelinkInactiveError,
    create_sharelink,
    upload_document,
    validate_sharelink,
)


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class TestUploadDocument(TestCase):
    def setUp(self):
        self.user = Account.objects.create_user(username="testuser", password="pass")
        self.pet = Pet.objects.create(owner=self.user, name="testpet", pet_type="dog")
    
    def test_invalid_file_type_rejected(self):
        file=SimpleUploadedFile("test.html",b"x"*100,content_type="test/html")
        with self.assertRaises(TypeError):
            upload_document(pet=self.pet,
                                   file=file,
                                   name="test_document",
                                   file_type="o")
    
    def test_file_too_large(self):
        file=SimpleUploadedFile("test.jpeg",b"x"*(4*1024*1024),content_type="image/jpeg")
        with self.assertRaises(MemoryError):
            upload_document(pet=self.pet,
                            file=file,
                            name="test_document",
                            file_type="o")
             
    def test_was_document_uploaded(self):
        file=SimpleUploadedFile("test.jpg",b"x"*100,content_type="image/jpeg")
        document = upload_document(pet=self.pet,
                        file=file,
                        name="test_document",
                        file_type="o")
        #check document db record created
        self.assertTrue(Document.objects.filter(pk=document.pk).exists())
        #check actual file exists
        self.assertTrue(document.file.storage.exists(document.file.name))
    
    def test_document_rollback(self):
        file=SimpleUploadedFile("test.jpg",b"x"*100,content_type="image/jpeg")

        with patch.object(FieldFile, 'delete') as mock_delete:
            with patch.object(Document, 'save', side_effect=Exception("DB error")):
                with self.assertRaises(RuntimeError):
                    upload_document(pet=self.pet, file=file, name="test", file_type="vr")
            mock_delete.assert_called_once_with(save=False)
    
    
        
        
        