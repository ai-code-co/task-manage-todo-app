import csv
import io
import logging
from time import perf_counter

from django.shortcuts import render
from django.utils.timezone import now
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Task
from .pagination import TaskPagination
from .serializers import TaskSerializer

logger = logging.getLogger(__name__)


def index(request):
    return render(request, "index.html")


class TaskViewSet(ModelViewSet):
    queryset = Task.objects.filter(is_deleted=False).order_by("-updated_at")
    serializer_class = TaskSerializer
    pagination_class = TaskPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "priority"]
    search_fields = ["title", "description"]
    ordering_fields = ["priority", "status", "created_at", "updated_at", "deleted_at"]
    ordering = ["-updated_at"]

    def get_queryset(self):
        return self.queryset

    def list(self, request, *args, **kwargs):
        total_started = perf_counter()

        queryset_started = perf_counter()
        queryset = self.filter_queryset(self.get_queryset())
        queryset_ms = (perf_counter() - queryset_started) * 1000

        pagination_started = perf_counter()
        page = self.paginate_queryset(queryset)
        pagination_ms = (perf_counter() - pagination_started) * 1000

        serialization_started = perf_counter()
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            response = Response(serializer.data)
        serialization_ms = (perf_counter() - serialization_started) * 1000

        logger.info(
            "Task list timing: queryset=%.2fms pagination=%.2fms serialization=%.2fms total=%.2fms",
            queryset_ms,
            pagination_ms,
            serialization_ms,
            (perf_counter() - total_started) * 1000,
        )
        return response

    def _is_completion_patch(self, request):
        return set(request.data.keys()) == {"status"} and request.data.get("status") == Task.STATUS_COMPLETED

    def _complete_task(self, pk):
        completion_started = perf_counter()
        completed_at = now()
        queryset = Task.objects.filter(pk=pk, is_deleted=False)
        updated = queryset.exclude(status=Task.STATUS_COMPLETED).update(
            status=Task.STATUS_COMPLETED,
            updated_at=completed_at,
        )

        if updated:
            logger.info(
                "Task completion timing: task_id=%s update=%.2fms already_completed=false",
                pk,
                (perf_counter() - completion_started) * 1000,
            )
            return True

        if queryset.exists():
            logger.info(
                "Task completion timing: task_id=%s update=%.2fms already_completed=true",
                pk,
                (perf_counter() - completion_started) * 1000,
            )
            return True

        logger.info(
            "Task completion timing: task_id=%s update=%.2fms found=false",
            pk,
            (perf_counter() - completion_started) * 1000,
        )
        return False

    def create(self, request, *args, **kwargs):
        is_many = isinstance(request.data, list)

        serializer = self.get_serializer(data=request.data, many=is_many)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        total_started = perf_counter()
        pk = kwargs["pk"]

        if self._is_completion_patch(request):
            completed = self._complete_task(pk)
            if not completed:
                return Response(status=status.HTTP_404_NOT_FOUND)

            logger.info(
                "Task partial_update timing: task_id=%s total=%.2fms fast_path=true",
                pk,
                (perf_counter() - total_started) * 1000,
            )
            return Response({"id": int(pk), "status": Task.STATUS_COMPLETED}, status=status.HTTP_200_OK)

        object_started = perf_counter()
        instance = self.get_object()
        object_ms = (perf_counter() - object_started) * 1000

        validation_started = perf_counter()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validation_ms = (perf_counter() - validation_started) * 1000

        save_started = perf_counter()
        serializer.save()
        save_ms = (perf_counter() - save_started) * 1000

        serialization_started = perf_counter()
        response = Response(serializer.data)
        serialization_ms = (perf_counter() - serialization_started) * 1000

        logger.info(
            "Task partial_update timing: task_id=%s get_object=%.2fms validation=%.2fms save=%.2fms serialization=%.2fms total=%.2fms fast_path=false",
            pk,
            object_ms,
            validation_ms,
            save_ms,
            serialization_ms,
            (perf_counter() - total_started) * 1000,
        )
        return response

    def destroy(self, request, *args, **kwargs):
        deleted_at = now()
        deleted = Task.objects.filter(pk=kwargs["pk"], is_deleted=False).update(
            is_deleted=True,
            deleted_at=deleted_at,
            updated_at=deleted_at,
        )
        if not deleted:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response({"message": "Task deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        if not self._complete_task(pk):
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"], url_path="upload-csv")
    def upload_csv(self, request):
        file = request.FILES.get("file")

        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        if file.size > 2 * 1024 * 1024:
            return Response({"error": "File size should be less than 2MB"}, status=status.HTTP_400_BAD_REQUEST)

        if not file.name.endswith(".csv"):
            return Response({"error": "only CSV files are allowed"}, status=status.HTTP_400_BAD_REQUEST)

        decoded_file = file.read().decode("utf-8")
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)

        tasks = []
        errors = []

        for idx, row in enumerate(reader, start=1):
            if not any(row.values()):
                continue

            serializer = self.get_serializer(data=row)

            if serializer.is_valid():
                tasks.append(Task(**serializer.validated_data))
            else:
                errors.append({
                    "row": idx,
                    "error": serializer.errors,
                })

        Task.objects.bulk_create(tasks)

        return Response(
            {
                "created_count": len(tasks),
                "errors": errors,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="bulk-delete")
    def bulk_delete(self, request):
        ids = request.data.get("ids", [])

        if not ids:
            return Response({"error": "No IDs provided"}, status=status.HTTP_400_BAD_REQUEST)

        deleted_at = now()
        deleted_count = Task.objects.filter(id__in=ids, is_deleted=False).update(
            is_deleted=True,
            deleted_at=deleted_at,
            updated_at=deleted_at,
        )

        return Response({"deleted_count": deleted_count}, status=status.HTTP_200_OK)
