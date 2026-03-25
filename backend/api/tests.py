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
                    upload_document(pet=self.pet, file=file, name="test", file_type="o")
            mock_delete.assert_called_once_with(save=False)
    
class TestCreateSharelink(TestCase):
    def setUp(self):
        self.user = Account.objects.create_user(username="testuser", password="pass")
        self.pet = Pet.objects.create(owner=self.user, name="testpet", pet_type="dog")
        self.doc1 = Document.objects.create(pet=self.pet, name="doc1", file_type="vr")
        self.doc2 = Document.objects.create(pet=self.pet, name="doc2", file_type="vr")
        self.document_ids = [self.doc1.pk, self.doc2.pk]
    
    def test_incorrect_document_number(self):
        invalid_ids = [self.document_ids[0],99999]
        with self.assertRaises(ValueError):
            create_sharelink(pet=self.pet,
                             document_ids=invalid_ids,
                             expires_at=timezone.now()+timedelta(days=7))
    
    def test_invalid_expiry_date(self):
        with self.assertRaises(ValueError):
            create_sharelink(pet=self.pet,
                             document_ids=self.document_ids,
                             expires_at=timezone.now()-timedelta(days=1))
    
    def test_sharelink_creation(self):
        sharelink = create_sharelink(pet=self.pet,
                                     document_ids=self.document_ids,
                                     expires_at=timezone.now()+timedelta(days=7))
        self.assertTrue(Sharelink.objects.filter(token=sharelink.token).exists())
        self.assertEqual(set(sharelink.documents.values_list('pk', flat=True)), 
                         set(self.document_ids))
    
    def test_documents_from_diff_pet_rejected(self):
        other_pet = Pet.objects.create(owner=self.user, name="otherpet", pet_type="cat")
        other_doc = Document.objects.create(pet=other_pet, name="other", file_type="o")
        with self.assertRaises(ValueError):
            create_sharelink(pet=self.pet,
                             document_ids=[other_doc.pk],
                             expires_at=timezone.now()+timedelta(days=7))
    
        
        
        