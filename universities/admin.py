from django.contrib import admin
from .models import University

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = (
        "university_id",
        "legacy_id",
        "name",
        "campus_name",
        "region",
        "is_active",
    )
    search_fields = ("name", "short_name", "address")
    list_filter = ("region", "university_type", "is_active")
    ordering = ("name",)
