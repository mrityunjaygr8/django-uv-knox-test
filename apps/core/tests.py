from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from knox.models import AuthToken

from .models import Tag, Category


class TagModelTest(TestCase):
    """Test cases for Tag model."""

    def setUp(self):
        self.tag = Tag.objects.create(
            name="Test Tag",
            slug="test-tag",
            description="A test tag for testing"
        )

    def test_tag_creation(self):
        """Test that a tag can be created successfully."""
        self.assertEqual(self.tag.name, "Test Tag")
        self.assertEqual(self.tag.slug, "test-tag")
        self.assertEqual(str(self.tag), "Test Tag")
        self.assertFalse(self.tag.is_deleted)

    def test_tag_soft_delete(self):
        """Test that tag soft delete works correctly."""
        self.tag.delete()
        self.assertTrue(self.tag.is_deleted)
        self.assertIsNotNone(self.tag.deleted_at)

    def test_tag_hard_delete(self):
        """Test that tag hard delete works correctly."""
        tag_id = self.tag.id
        self.tag.hard_delete()
        self.assertFalse(Tag.objects.filter(id=tag_id).exists())


class CategoryModelTest(TestCase):
    """Test cases for Category model."""

    def setUp(self):
        self.parent_category = Category.objects.create(
            name="Parent Category",
            slug="parent-category",
            description="A parent category"
        )
        self.child_category = Category.objects.create(
            name="Child Category",
            slug="child-category",
            description="A child category",
            parent=self.parent_category
        )

    def test_category_creation(self):
        """Test that a category can be created successfully."""
        self.assertEqual(self.parent_category.name, "Parent Category")
        self.assertEqual(str(self.parent_category), "Parent Category")
        self.assertTrue(self.parent_category.is_active)
        self.assertFalse(self.parent_category.is_deleted)

    def test_category_hierarchy(self):
        """Test category hierarchy functionality."""
        self.assertEqual(self.child_category.parent, self.parent_category)
        self.assertEqual(str(self.child_category), "Parent Category > Child Category")
        self.assertIn(self.child_category, self.parent_category.children.all())

    def test_category_full_path(self):
        """Test get_full_path method."""
        expected_path = "Parent Category > Child Category"
        self.assertEqual(self.child_category.get_full_path(), expected_path)

    def test_category_soft_delete(self):
        """Test that category soft delete works correctly."""
        self.parent_category.delete()
        self.assertTrue(self.parent_category.is_deleted)
        self.assertIsNotNone(self.parent_category.deleted_at)


class TagAPITest(APITestCase):
    """Test cases for Tag API endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.instance, self.token = AuthToken.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

        self.tag = Tag.objects.create(
            name="Test Tag",
            slug="test-tag",
            description="A test tag"
        )

    def test_get_tag_list(self):
        """Test retrieving tag list."""
        url = reverse('tag-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], "Test Tag")

    def test_create_tag(self):
        """Test creating a new tag."""
        url = reverse('tag-list')
        data = {
            'name': 'New Tag',
            'slug': 'new-tag',
            'description': 'A new test tag'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tag.objects.count(), 2)
        self.assertEqual(response.data['name'], 'New Tag')

    def test_get_tag_detail(self):
        """Test retrieving a specific tag."""
        url = reverse('tag-detail', kwargs={'pk': self.tag.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.tag.name)

    def test_update_tag(self):
        """Test updating a tag."""
        url = reverse('tag-detail', kwargs={'pk': self.tag.pk})
        data = {
            'name': 'Updated Tag',
            'slug': 'updated-tag',
            'description': 'Updated description'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.tag.refresh_from_db()
        self.assertEqual(self.tag.name, 'Updated Tag')

    def test_delete_tag(self):
        """Test deleting a tag (soft delete)."""
        url = reverse('tag-detail', kwargs={'pk': self.tag.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.tag.refresh_from_db()
        self.assertTrue(self.tag.is_deleted)

    def test_tag_popular_action(self):
        """Test popular tags endpoint."""
        url = reverse('tag-popular')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_create_tag_without_authentication(self):
        """Test that creating a tag requires authentication."""
        self.client.credentials()  # Remove authentication
        url = reverse('tag-list')
        data = {
            'name': 'Unauthorized Tag',
            'slug': 'unauthorized-tag'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CategoryAPITest(APITestCase):
    """Test cases for Category API endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.instance, self.token = AuthToken.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

        self.parent_category = Category.objects.create(
            name="Parent Category",
            slug="parent-category",
            description="A parent category"
        )
        self.child_category = Category.objects.create(
            name="Child Category",
            slug="child-category",
            description="A child category",
            parent=self.parent_category
        )

    def test_get_category_list(self):
        """Test retrieving category list."""
        url = reverse('category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_create_category(self):
        """Test creating a new category."""
        url = reverse('category-list')
        data = {
            'name': 'New Category',
            'slug': 'new-category',
            'description': 'A new test category',
            'is_active': True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 3)

    def test_get_root_categories(self):
        """Test retrieving root categories."""
        url = reverse('category-root-categories')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Parent Category')

    def test_get_category_children(self):
        """Test retrieving category children."""
        url = reverse('category-children', kwargs={'pk': self.parent_category.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Child Category')

    def test_get_category_full_path(self):
        """Test retrieving category full path."""
        url = reverse('category-full-path', kwargs={'pk': self.child_category.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_path'], 'Parent Category > Child Category')

    def test_category_search(self):
        """Test category search functionality."""
        url = reverse('category-list')
        response = self.client.get(url, {'search': 'Parent'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Parent Category')

    def test_category_filter_by_parent(self):
        """Test filtering categories by parent."""
        url = reverse('category-list')
        response = self.client.get(url, {'parent': self.parent_category.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Child Category')

    def test_create_category_without_authentication(self):
        """Test that creating a category requires authentication."""
        self.client.credentials()  # Remove authentication
        url = reverse('category-list')
        data = {
            'name': 'Unauthorized Category',
            'slug': 'unauthorized-category'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
