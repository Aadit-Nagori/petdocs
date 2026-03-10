from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views import generic

from .models import Pet


@login_required
def pet_list(request: HttpRequest) -> HttpResponse:
    pets = Pet.objects.filter(owner=request.user)
    return render(request, "api/pet_list.html", {"pets": pets})

@login_required
def pet_detail(request: HttpRequest, pk: int) -> HttpResponse:
    pet = get_object_or_404(Pet, pk=pk, owner=request.user)
    return render(request, "api/pet_detail.html", {"pet": pet})


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
        
