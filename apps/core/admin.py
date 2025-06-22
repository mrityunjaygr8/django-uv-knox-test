from django.contrib import admin
from .models import Tag, Category


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Admin configuration for Tag model.
    """
    list_display = ['name', 'slug', 'created', 'is_deleted']
    list_filter = ['is_deleted', 'created', 'modified']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created', 'modified']
    ordering = ['name']

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description')
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
        ('Soft Delete', {
            'fields': ('is_deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """
        Show all tags including soft-deleted ones in admin.
        """
        return self.model.objects.all()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for Category model with hierarchical display.
    """
    list_display = ['name', 'parent', 'slug', 'is_active', 'created', 'is_deleted']
    list_filter = ['is_active', 'is_deleted', 'parent', 'created', 'modified']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created', 'modified', 'get_full_path']
    ordering = ['name']

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'parent', 'is_active')
        }),
        ('Hierarchy', {
            'fields': ('get_full_path',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
        ('Soft Delete', {
            'fields': ('is_deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )

    def get_full_path(self, obj):
        """
        Display the full hierarchical path in admin.
        """
        return obj.get_full_path()
    get_full_path.short_description = 'Full Path'

    def get_queryset(self, request):
        """
        Show all categories including soft-deleted ones in admin.
        """
        return self.model.objects.all()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Customize the parent field to exclude the current object to prevent self-reference.
        """
        if db_field.name == "parent":
            # Get the object ID from the URL if we're editing an existing object
            if request.resolver_match.kwargs.get('object_id'):
                obj_id = request.resolver_match.kwargs['object_id']
                kwargs["queryset"] = Category.objects.filter(is_deleted=False).exclude(pk=obj_id)
            else:
                kwargs["queryset"] = Category.objects.filter(is_deleted=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
