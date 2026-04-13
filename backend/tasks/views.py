from django.shortcuts import render


# Create your views here.
from rest_framework import viewsets,status
from rest_framework.response import Response
from django.utils.timezone import now
from .models import Task
from .serializers import TaskSerializer
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination

from rest_framework.decorators import action
class TaskPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 10

def index(request):
    return render(request, 'index.html')

class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all().order_by("-created_at")
    serializer_class = TaskSerializer
    pagination_class = TaskPagination
    # permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "priority"]
    search_fields = ["title", "description"]
    ordering_fields = ["priority", "status", "created_at", "updated_at","deleted_at"]

    # 🔹 IMPORTANT: Hide deleted tasks
    def get_queryset(self):
        return Task.objects.filter(is_deleted=False)

    # 🔹 CREATE (POST /tasks/)
    def create(self, request, *args, **kwargs):
        is_many = isinstance(request.data, list)

        serializer = self.get_serializer(data=request.data, many=is_many)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    # 🔹 RETRIEVE (GET /tasks/{id}/)
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    # 🔹 UPDATE (PUT /tasks/{id}/)
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # 🔹 PARTIAL UPDATE (PATCH /tasks/{id}/)
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # 🔥 SOFT DELETE (DELETE /tasks/{id}/)
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.deleted_at = now()
        instance.save()
        return Response(
            {"message": "Task deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
    @action(detail=False, methods=['post'],url_path='upload-csv')
    def upload_csv(self, request):
        file = request.FILES.get('file')

        

        if not file:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)  
        
        if file.size > 2 * 1024 * 1024:
            return Response({'error': 'File size should be less than 2MB'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not file.name.endswith('.csv'):
            return Response({'error': 'only CSV files are allowed'}, status=status.HTTP_400_BAD_REQUEST)
        
        import csv, io
        decoded_file = file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)

        tasks = []
        errors = []

        for idx, row in enumerate(reader, start=1):

            # skip empty rows
            if not any(row.values()):
                continue

            serializer = self.get_serializer(data=row)

            if serializer.is_valid():
                tasks.append(Task(**serializer.validated_data))
            else:
                errors.append({
                    "row": idx,
                    "error": serializer.errors
                })

        # bulk insert
        Task.objects.bulk_create(tasks)
        # serializer = self.get_serializer(data=[t.__dict__ for t in tasks], many=True)
        # serializer.is_valid(raise_exception=True)
        # serializer.save()

        # bulk_serializer = self.get_serializer(data=tasks, many=True)
        # bulk_serializer.is_valid(raise_exception=True)
        # bulk_serializer.save()
        

        return Response({
            "created_count": len(tasks),
            "errors": errors
        }, status=status.HTTP_201_CREATED)