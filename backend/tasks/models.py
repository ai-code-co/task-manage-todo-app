from django.db import models


class Task(models.Model):
    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_COMPLETED, "Completed"),
    )

    PRIORITY_CHOICES = (
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="medium")

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def soft_delete(self):
        from django.utils.timezone import now

        deleted_at = now()
        self.is_deleted = True
        self.deleted_at = deleted_at
        self.updated_at = deleted_at
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])

    def __str__(self):
        return self.title

    class Meta:
        indexes = [
            models.Index(fields=["is_deleted", "updated_at"]),
            models.Index(fields=["status", "updated_at"]),
            models.Index(fields=["priority", "updated_at"]),
        ]
