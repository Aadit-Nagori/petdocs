from django import forms

from .models import Document, Sharelink


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['file', 'name', 'file_type']

class SharelinkForm(forms.ModelForm):
    def __init__(self, pet, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['documents'].queryset = Document.objects.filter(pet=pet)
    class Meta:
        model = Sharelink
        fields = ['documents', 'expires_at']

