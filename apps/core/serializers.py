from rest_framework import serializers
from .models import Tag, Category


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for Tag model.
    """

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'description', 'created', 'modified']
        read_only_fields = ['id', 'created', 'modified']

    def validate_name(self, value):
        """
        Validate that tag name is unique and not empty.
        """
        if not value.strip():
            raise serializers.ValidationError("Tag name cannot be empty.")
        return value.strip()


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model with hierarchical support.
    """
    children = serializers.SerializerMethodField()
    full_path = serializers.SerializerMethodField()
    parent_name = serializers.CharField(source='parent.name', read_only=True)

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'parent_name',
            'is_active', 'children', 'full_path', 'created', 'modified'
        ]
        read_only_fields = ['id', 'created', 'modified', 'parent_name', 'children', 'full_path']

    def get_children(self, obj):
        """
        Get child categories.
        """
        children = obj.children.filter(is_deleted=False, is_active=True)
        return CategorySerializer(children, many=True, context=self.context).data

    def get_full_path(self, obj):
        """
        Get the full hierarchical path of the category.
        """
        return obj.get_full_path()

    def validate_name(self, value):
        """
        Validate that category name is not empty.
        """
        if not value.strip():
            raise serializers.ValidationError("Category name cannot be empty.")
        return value.strip()

    def validate(self, attrs):
        """
        Validate that a category cannot be its own parent.
        """
        parent = attrs.get('parent')
        if parent and self.instance and parent.id == self.instance.id:
            raise serializers.ValidationError("A category cannot be its own parent.")

        # Prevent circular references
        if parent and self.instance:
            current_parent = parent
            while current_parent:
                if current_parent.id == self.instance.id:
                    raise serializers.ValidationError("Circular reference detected in category hierarchy.")
                current_parent = current_parent.parent

        return attrs


class CategoryTreeSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying category tree structure.
    """
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'children']

    def get_children(self, obj):
        """
        Recursively get all child categories.
        """
        children = obj.children.filter(is_deleted=False, is_active=True)
        return CategoryTreeSerializer(children, many=True, context=self.context).data
