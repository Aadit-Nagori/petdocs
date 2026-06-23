import uuid
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
    deactivate_sharelink,
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

class TestValidateSharelink(TestCase):
    def setUp(self):
        self.user = Account.objects.create_user(username="testuser", password="pass")
        self.pet = Pet.objects.create(owner=self.user, name="testpet", pet_type="dog")
        self.doc = Document.objects.create(pet=self.pet, name="doc1", file_type="vr")
        self.sharelink = Sharelink.objects.create(
            pet=self.pet,
            expires_at=timezone.now() + timedelta(days=7)
        )
        self.sharelink.documents.set([self.doc])

    def test_valid_sharelink_token(self):
        sharelink = validate_sharelink(token=self.sharelink.token)
        self.assertTrue(Sharelink.objects.filter(token=sharelink.token).exists())
        self.assertEqual(set(sharelink.documents.values_list('pk', flat=True)), 
                         set(self.sharelink.documents.values_list('pk',flat=True)))
    
    def test_nonexistent_sharelink(self):
        with self.assertRaises(ValueError):
            validate_sharelink(token=uuid.uuid4())
    
    def test_expired_sharelink(self):
        self.sharelink.expires_at = timezone.now()-timedelta(seconds=100)
        self.sharelink.save()
        with self.assertRaises(SharelinkExpiredError):
            validate_sharelink(token=self.sharelink.token)
    
    def test_deactivate_sharelink_other_pet(self):
        other_pet = Pet.objects.create(owner=self.user, name="otherpet", pet_type="cat")
        with self.assertRaises(PermissionError):
            deactivate_sharelink(pet=other_pet,sharelink=self.sharelink)
    
    def test_deactivate_sharelink(self):
        deactivate_sharelink(pet=self.pet,sharelink=self.sharelink)
        self.assertFalse(self.sharelink.is_active)
    
    def test_deactivated_sharelink(self):
        deactivate_sharelink(pet=self.pet,sharelink=self.sharelink)
        with self.assertRaises(SharelinkInactiveError):
            validate_sharelink(token=self.sharelink.token)


class TestAuthentication(TestCase):
    def setUp(self):
        self.user = Account.objects.create_user(username="testuser", password="pass")
        self.pet = Pet.objects.create(owner=self.user, name="testpet", pet_type="dog")
        self.doc = Document.objects.create(pet=self.pet, name="doc1", file_type="vr")

    def test_unauthenticated_pet_list_redirects(self):
        response = self.client.get('/pets/')
        self.assertRedirects(response, '/accounts/login/?next=/pets/')

    def test_unauthenticated_pet_detail_redirects(self):
        response = self.client.get(f'/pets/{self.pet.pk}/')
        self.assertRedirects(response, f'/accounts/login/?next=/pets/{self.pet.pk}/')

    def test_unauthenticated_document_add_redirects(self):
        response = self.client.get(f'/pets/{self.pet.pk}/documents/add/')
        self.assertRedirects(
            response, f'/accounts/login/?next=/pets/{self.pet.pk}/documents/add/'
        )

    def test_unauthenticated_sharelink_create_redirects(self):
        response = self.client.get(f'/pets/{self.pet.pk}/sharelink/create/')
        self.assertRedirects(
            response, f'/accounts/login/?next=/pets/{self.pet.pk}/sharelink/create/'
        )


class TestOwnership(TestCase):
    def setUp(self):
        self.user_a = Account.objects.create_user(username="usera", password="pass")
        self.user_b = Account.objects.create_user(username="userb", password="pass")
        self.pet_a = Pet.objects.create(owner=self.user_a, name="peta", pet_type="dog")
        self.doc_a = Document.objects.create(
            pet=self.pet_a, name="doc1", file_type="vr"
        )

    def test_user_b_cannot_view_user_a_pet(self):
        self.client.force_login(self.user_b)
        response = self.client.get(f'/pets/{self.pet_a.pk}/')
        self.assertEqual(response.status_code, 404)

    def test_user_b_cannot_add_document_to_user_a_pet(self):
        self.client.force_login(self.user_b)
        response = self.client.get(f'/pets/{self.pet_a.pk}/documents/add/')
        self.assertEqual(response.status_code, 404)

    def test_user_b_cannot_delete_user_a_document(self):
        self.client.force_login(self.user_b)
        response = self.client.post(
            f'/pets/{self.pet_a.pk}/documents/{self.doc_a.pk}/delete/'
        )
        self.assertEqual(response.status_code, 404)

    def test_user_b_cannot_create_sharelink_for_user_a_pet(self):
        self.client.force_login(self.user_b)
        response = self.client.get(f'/pets/{self.pet_a.pk}/sharelink/create/')
        self.assertEqual(response.status_code, 404)


# TestPublicSharelinkView — write this following the pattern above
# setUp needs: user, pet, doc, and a Sharelink with a token
# Tests needed:
#   - valid token returns 200 without authentication
#   - invalid token returns 404
#   - expired token renders sharelink_expired.html
#   - inactive token renders sharelink_inactive.html

class TestPublicSharelinkView(TestCase):
    def setUp(self):
        self.user = Account.objects.create_user(username="user", password="pass")
        self.pet = Pet.objects.create(owner=self.user, name="pet", pet_type="dog")
        self.doc = Document.objects.create(
            pet=self.pet, name="doc1", file_type="vr", file="documents/1/1/test.jpg"
        )
        self.sharelink = Sharelink.objects.create(pet=self.pet,
            expires_at=timezone.now() + timedelta(days=7))
        self.sharelink.documents.set([self.doc])
        

    def test_valid_token_view(self):
        response = self.client.get(f'/share/{self.sharelink.token}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'api/sharelink_view.html')
    
    def test_invalid_token_view(self):
        response = self.client.get(f'/share/{uuid.uuid4()}/')
        self.assertEqual(response.status_code, 404)
    
    def test_inactive_token_view(self):
        deactivate_sharelink(self.pet,self.sharelink)
        response = self.client.get(f'/share/{self.sharelink.token}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'api/sharelink_inactive.html')
    
    def test_expired_token_view(self):
        self.sharelink.expires_at = timezone.now() - timedelta(seconds=100)
        self.sharelink.save()
        response = self.client.get(f'/share/{self.sharelink.token}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'api/sharelink_expired.html')
        