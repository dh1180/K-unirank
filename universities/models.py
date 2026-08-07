from django.db import models

class University(models.Model):
    university_id = models.BigAutoField(primary_key=True)

    legacy_id = models.BigIntegerField(
        unique=True,
        null=True,
        blank=True,
    )

    parent_university = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campuses",
    )

    name = models.CharField(max_length=150)
    short_name = models.CharField(max_length=100, null=True, blank=True)
    campus_name = models.CharField(max_length=100, null=True, blank=True)

    address = models.CharField(max_length=255, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    university_type = models.CharField(max_length=50, null=True, blank=True)

    # ex) university/logos/가천대.svg
    logo_path = models.CharField(max_length=255, null=True, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "universities"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["region"]),
        ]

    def __str__(self):
        if self.campus_name:
            return f"{self.name} ({self.campus_name})"
        return self.name
