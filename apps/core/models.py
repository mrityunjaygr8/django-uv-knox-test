from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Abstract base class that provides self-updating 'created' and 'modified' fields.
    """
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Abstract base class that provides soft delete functionality.
    """
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """
        Soft delete the object by setting is_deleted to True.
        """
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using)

    def hard_delete(self, using=None, keep_parents=False):
        """
        Permanently delete the object from the database.
        """
        super().delete(using=using, keep_parents=keep_parents)


class BaseModel(TimeStampedModel, SoftDeleteModel):
    """
    Abstract base class that combines timestamp and soft delete functionality.
    """
    class Meta:
        abstract = True

    @property
    def created_utc(self):
        """
        Returns creation time in UTC (timezone-aware).
        Useful for API responses where you want explicit UTC timestamps.
        """
        return self.created.astimezone(timezone.get_default_timezone())

    @property
    def created_local(self):
        """
        Returns creation time in current timezone.
        Django automatically handles timezone conversion in templates.
        """
        return timezone.localtime(self.created)

    @property
    def modified_utc(self):
        """
        Returns modification time in UTC (timezone-aware).
        """
        return self.modified.astimezone(timezone.get_default_timezone())

    @property
    def modified_local(self):
        """
        Returns modification time in current timezone.
        """
        return timezone.localtime(self.modified)


class Tag(BaseModel):
    """
    Simple tag model for categorizing content.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Category(BaseModel):
    """
    Hierarchical category model.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]
        unique_together = [["name", "parent"]]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def get_full_path(self):
        """
        Returns the full path of the category including parent categories.
        """
        path = [self.name]
        parent = self.parent
        while parent:
            path.append(parent.name)
            parent = parent.parent
        return " > ".join(reversed(path))
