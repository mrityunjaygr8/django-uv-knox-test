from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """
    Inline admin for UserProfile model.
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = (
        'bio', 'birth_date', 'phone_number', 'website', 'avatar',
        'country', 'city', 'is_public', 'show_email',
        'email_notifications', 'marketing_emails'
    )


class UserAdmin(BaseUserAdmin):
    """
    Extended User admin with UserProfile inline.
    """
    inlines = (UserProfileInline,)
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'is_staff', 'is_active', 'date_joined', 'get_profile_status'
    )
    list_filter = BaseUserAdmin.list_filter + ('profile__is_public',)

    def get_profile_status(self, obj):
        """
        Display profile public status.
        """
        if hasattr(obj, 'profile'):
            return "Public" if obj.profile.is_public else "Private"
        return "No Profile"
    get_profile_status.short_description = 'Profile Status'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin configuration for UserProfile model.
    """
    list_display = [
        'user', 'get_full_name', 'country', 'city', 'is_public',
        'email_notifications', 'created', 'is_deleted'
    ]
    list_filter = [
        'is_public', 'email_notifications', 'marketing_emails',
        'country', 'is_deleted', 'created', 'modified'
    ]
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'bio']
    readonly_fields = ['created', 'modified', 'get_full_name']
    ordering = ['-created']

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'get_full_name')
        }),
        ('Profile Details', {
            'fields': ('bio', 'birth_date', 'phone_number', 'website', 'avatar')
        }),
        ('Location', {
            'fields': ('country', 'city'),
            'classes': ('collapse',)
        }),
        ('Privacy & Preferences', {
            'fields': ('is_public', 'show_email', 'email_notifications', 'marketing_emails')
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

    def get_full_name(self, obj):
        """
        Display the user's full name.
        """
        return obj.full_name
    get_full_name.short_description = 'Full Name'

    def get_queryset(self, request):
        """
        Show all profiles including soft-deleted ones in admin.
        """
        return self.model.objects.all()


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
