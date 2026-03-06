from django.contrib import admin

from .models import Document, Pet, Sharelink


class DocumentInLine(admin.TabularInline):
    model = Document

class SharelinkInLine(admin.TabularInline):
    model = Sharelink

@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_filter = ["owner", "pet_type"]
    list_display = ["name", "owner", "pet_type"]
    inlines = [DocumentInLine, SharelinkInLine]

@admin.register(Sharelink)
class SharelinkAdmin(admin.ModelAdmin):
    list_display = ["pet", "token", "created_at", "is_active", "display_expired"]
    readonly_fields = ["token", "created_at", "display_expired"]
    fieldsets = [
        ("Main Info", {"fields": ["pet", "token", "created_at", "expires_at", "display_expired", "is_active"]}),
        ("Documents", {"fields": ["documents"]})
    ]
    
    @admin.display(description="Expired?", boolean=True)
    def display_expired(self,obj):
        return obj.is_expired

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["pet", "name", "file_type", "uploaded_at"]
    readonly_fields = ["uploaded_at"]
    fieldsets = [
        ("Main Info", {"fields": ["pet", "name", "file_type", "uploaded_at"]}),
        ("File Info", {"fields": ["file"]})
    ]
