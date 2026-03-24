from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import generic

from .forms import DocumentForm, SharelinkForm
from .models import Document, Pet, Sharelink
from .services import (
    SharelinkExpiredError,
    SharelinkInactiveError,
    create_sharelink,
    deactivate_sharelink,
    delete_document,
    generate_qrcode,
    upload_document,
    validate_sharelink,
)


@login_required
def pet_list(request: HttpRequest) -> HttpResponse:
    pets = Pet.objects.filter(owner=request.user)
    return render(request, "api/pet_list.html", {"pets": pets})

@login_required
def pet_detail(request: HttpRequest, pk: int) -> HttpResponse:
    pet = get_object_or_404(Pet, pk=pk, owner=request.user)
    documents = Document.objects.filter(pet=pet)
    sharelinks = Sharelink.objects.filter(pet=pet)
    return render(request, "api/pet_detail.html", {"pet": pet, "documents": documents, 
                                                   "sharelinks": sharelinks})


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

@login_required
def sharelink_create(request: HttpRequest, pk: int) -> HttpResponse:
    pet = get_object_or_404(Pet, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = SharelinkForm(pet, request.POST)
        if form.is_valid():
            try:
                sharelink = create_sharelink(
                    pet=pet,
                    document_ids=list(form.cleaned_data['documents']
                                      .values_list('pk', flat=True)),
                    expires_at=form.cleaned_data['expires_at']
                )
                url = request.build_absolute_uri(reverse('sharelink_view', 
                                                 args=[sharelink.token]))
                qr_code = generate_qrcode(url)
                return render(request, 'api/sharelink_created.html', 
                                {'sharelink': sharelink, 
                                'url': url, 
                                'qr_code': qr_code, 
                                'pet': pet})
            except Exception as e:
                print(f"sharelink create failed with exception {e}")
    else:
        form = SharelinkForm(pet)
    return render(request,'api/sharelink_form.html', {"form":form, "pet": pet})

@login_required
def sharelink_quickshare(request: HttpRequest, pk: int) -> HttpResponse:
    pet = get_object_or_404(Pet,pk=pk,owner=request.user)
    if request.method == 'POST':
        documents = Document.objects.filter(pet=pet)
        document_ids = list(documents.values_list('pk',flat=True))
        try:
            sharelink = create_sharelink(
                pet=pet,
                document_ids=document_ids,
                expires_at=timezone.now()+timedelta(days=7)
            )
            url = request.build_absolute_uri(reverse('sharelink_view', 
                                                 args=[sharelink.token]))
            qr_code = generate_qrcode(url)
            return render(request, 'api/sharelink_created.html', 
                            {'sharelink': sharelink, 
                            'url': url, 
                            'qr_code': qr_code, 
                            'pet': pet})
        except Exception as e:
            print(f"quick share creation failed with {e}")
    else:
        return redirect('pets:pet_detail',pk=pk)

@login_required
def sharelink_deactivate(request: HttpRequest, pk: int, token: str) -> HttpResponse:
    pet = get_object_or_404(Pet, pk=pk, owner=request.user)
    sharelink = get_object_or_404(Sharelink,token=token,pet=pet)
    if request.method == 'POST':
        try:
            deactivate_sharelink(
                pet=pet,
                sharelink=sharelink
            )
        except Exception as e:
            print(f"sharelink deactivation failed with exception {e}")
    return redirect('pets:pet_detail',pk=pk)

def sharelink_view(request: HttpRequest, token: str) -> HttpResponse:
    try:
        sharelink = validate_sharelink(token)
    except SharelinkExpiredError:
        return render(request, 'api/sharelink_expired.html')
    except SharelinkInactiveError:
        return render(request, 'api/sharelink_inactive.html')
    except ValueError as exc:
        raise Http404 from exc
    documents = sharelink.documents.all()
    return render(request, 'api/sharelink_view.html', {
        'sharelink': sharelink,
        'pet': sharelink.pet,
        'documents': documents
    })
