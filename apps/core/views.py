from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Tag, Category
from .serializers import TagSerializer, CategorySerializer


class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tags.
    Provides CRUD operations for tags.
    """
    queryset = Tag.objects.filter(is_deleted=False)
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['name']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created']
    ordering = ['name']

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """
        Returns the most popular tags.
        """
        # This is a placeholder - implement your own logic
        popular_tags = self.get_queryset()[:10]
        serializer = self.get_serializer(popular_tags, many=True)
        return Response(serializer.data)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing categories.
    Provides CRUD operations for categories with hierarchical support.
    """
    queryset = Category.objects.filter(is_deleted=False, is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['parent', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created']
    ordering = ['name']

    @action(detail=False, methods=['get'])
    def root_categories(self, request):
        """
        Returns only root categories (categories without parent).
        """
        root_categories = self.get_queryset().filter(parent=None)
        serializer = self.get_serializer(root_categories, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """
        Returns child categories of the specified category.
        """
        category = self.get_object()
        children = category.children.filter(is_deleted=False, is_active=True)
        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def full_path(self, request, pk=None):
        """
        Returns the full path of the category.
        """
        category = self.get_object()
        return Response({
            'id': category.id,
            'full_path': category.get_full_path()
        })
