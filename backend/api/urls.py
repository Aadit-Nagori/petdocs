from django.urls import path

from . import views

app_name = "pets"
urlpatterns = [
    path("", views.pet_list, name="pet_list"),
    path("add/", views.PetCreate.as_view(), name="pet_create"),
    path("<int:pk>/", views.pet_detail, name="pet_detail"),
    path("<int:pk>/edit/", views.PetUpdate.as_view(), name="pet_update"),
    path("<int:pk>/delete/", views.PetDelete.as_view(), name="pet_delete"),
    path("<int:pk>/documents/add/", views.document_add, name="document_add"),
    path("<int:pk>/documents/<int:doc_pk>/delete/", views.document_delete, name="document_delete")  # noqa: E501
]
