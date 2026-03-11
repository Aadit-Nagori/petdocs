from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import generic

from .forms import DocumentForm
from .models import Document, Pet
from .services import delete_document, upload_document


@login_required
def pet_list(request: HttpRequest) -> HttpResponse:
    pets = Pet.objects.filter(owner=request.user)
    return render(request, "api/pet_list.html", {"pets": pets})

@login_required
def pet_detail(request: HttpRequest, pk: int) -> HttpResponse:
    pet = get_object_or_404(Pet, pk=pk, owner=request.user)
    documents = Document.objects.filter(pet=pet)
    return render(request, "api/pet_detail.html", {"pet": pet, "documents": documents})


class PetCreate(LoginRequiredMixin, generic.CreateView):
    template_name="api/pet_form.html"
    model = Pet
    fields = ['name', 'pet_type']
    success_url = reverse_lazy('pets:pet_list')
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

class PetUpdate(LoginRequiredMixin, generic.UpdateView):
    template_name="api/pet_form.html"
    model = Pet
    fields = ['name', 'pet_type']
    success_url = reverse_lazy('pets:pet_list')
    
    def get_queryset(self):
        return Pet.objects.filter(owner=self.request.user)

class PetDelete(LoginRequiredMixin, generic.DeleteView):
    template_name = "api/pet_confirm_delete.html"
    model = Pet
    success_url = reverse_lazy('pets:pet_list')
    
    def get_queryset(self):
        return Pet.objects.filter(owner=self.request.user)

@login_required
def document_add(request: HttpRequest, pk: int) -> HttpResponse:
    pet = get_object_or_404(Pet, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                upload_document(
                    pet=pet,
                    file=form.cleaned_data['file'],
                    name=form.cleaned_data['name'],
                    file_type=form.cleaned_data['file_type']
                )
                return redirect('pets:pet_detail', pk=pk)
            except Exception as e:
                print(f"file upload failed with exception {e}")
    else:
        form = DocumentForm()
    return render(request, 'api/document_form.html', {"form":form, "pet": pet})

@login_required
def document_delete(request: HttpRequest, pk:int, doc_pk: int) -> HttpResponse:
    pet = get_object_or_404(Pet, pk=pk, owner=request.user)
    document = get_object_or_404(Document,pk=doc_pk, pet=pet)
    if request.method == 'POST':
        try:
            delete_document(
                pet=pet,
                document=document
            )
        except Exception as e:
            print(f"file delete failed with exception {e}")
    return redirect('pets:pet_detail',pk=pk)
    
