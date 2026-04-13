from rest_framework import serializers
from .models import Task


class TaskListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        return Task.objects.bulk_create([Task(**task_data) for task_data in validated_data])


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"
        list_serializer_class = TaskListSerializer
        read_only_fields = ("created_at", "updated_at", "deleted_at", "is_deleted")

    # 🔹 Title Validation
    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Title is required and cannot be empty")
        return value

    # 🔹 Status Validation
    def validate_status(self, value):
        valid_status = [choice[0] for choice in Task.STATUS_CHOICES]
        if value not in valid_status:
            raise serializers.ValidationError(f"Status must be one of {valid_status}")
        return value

    # 🔹 Priority Validation
    def validate_priority(self, value):
        valid_priority = [choice[0] for choice in Task.PRIORITY_CHOICES]
        if value not in valid_priority:
            raise serializers.ValidationError(f"Priority must be one of {valid_priority}")
        return value

    # 🔹 Update Method (Handles PUT & PATCH)
    def update(self, instance, validated_data):
        # prevent updating deleted task
        if instance.is_deleted:
            raise serializers.ValidationError("Cannot update a deleted task")

        return super().update(instance, validated_data)
