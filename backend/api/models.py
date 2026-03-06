import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


# Create your models here.
def document_upload_path(instance,filename):
    return f"documents/{instance.pet.owner.id}/{instance.pet.id}/{filename}"



class Pet(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    PET_TYPE_CHOICES = {
        "dog" : "Dog",
        "cat" : "Cat",
        "bird": "Bird",
        "horse" : "Horse",
        "lizard" : "Lizard",
        "exotic" : "Exotic"
    }
    pet_type = models.CharField(max_length=20,choices=PET_TYPE_CHOICES)

class Document(models.Model):
    pet = models.ForeignKey(Pet,on_delete=models.CASCADE)
    file = models.FileField(upload_to=document_upload_path)
    name = models.CharField(max_length=50)
    DOCUMENT_TYPE_CHOICES = {
        "vr" : "Vaccination Record",
        "mh" : "Medical History",
        "ih" : "Immunization History",
        "p" : "Prescription",
        "o" : "other"
    }
    file_type = models.CharField(max_length=20,choices=DOCUMENT_TYPE_CHOICES)
    uploaded_at = models.DateTimeField(auto_now_add=True, editable=False)

class Sharelink(models.Model):
    pet = models.ForeignKey(Pet,on_delete=models.CASCADE)
    documents = models.ManyToManyField(Document)
    token = models.UUIDField(default=uuid.uuid4,editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    
    @property
    def is_expired(self):
        if not self.expires_at: 
            return False
        return timezone.now() > self.expires_at