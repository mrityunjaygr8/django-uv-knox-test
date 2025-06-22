from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from knox.models import AuthToken

from .models import UserProfile


class UserProfileModelTest(TestCase):
    """Test cases for UserProfile model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )

    def test_user_profile_creation(self):
        """Test that a user profile is automatically created when a user is created."""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)
        self.assertEqual(self.user.profile.user, self.user)

    def test_user_profile_default_values(self):
        """Test default values for user profile."""
        profile = self.user.profile
        self.assertTrue(profile.is_public)
        self.assertFalse(profile.show_email)
        self.assertTrue(profile.email_notifications)
        self.assertFalse(profile.marketing_emails)
        self.assertEqual(profile.bio, "")
        self.assertEqual(profile.phone_number, "")

    def test_full_name_property(self):
        """Test full_name property returns correct value."""
        profile = self.user.profile
        self.assertEqual(profile.full_name, "Test User")

        # Test with user without first/last name
        user_no_name = User.objects.create_user(
            username="noname",
            email="noname@example.com",
            password="testpass123"
        )
        self.assertEqual(user_no_name.profile.full_name, "noname")

    def test_display_name_property(self):
        """Test display_name property returns correct value."""
        profile = self.user.profile
        self.assertEqual(profile.display_name, "Test")

        # Test with user without first name
        user_no_first = User.objects.create_user(
            username="nofirst",
            email="nofirst@example.com",
            password="testpass123"
        )
        self.assertEqual(user_no_first.profile.display_name, "nofirst")

    def test_user_profile_str_method(self):
        """Test string representation of user profile."""
        profile = self.user.profile
        self.assertEqual(str(profile), "testuser's Profile")

    def test_user_profile_soft_delete(self):
        """Test that user profile soft delete works correctly."""
        profile = self.user.profile
        profile.delete()
        self.assertTrue(profile.is_deleted)
        self.assertIsNotNone(profile.deleted_at)


class UserAuthenticationAPITest(APITestCase):
    """Test cases for user authentication API."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )

    def test_user_login(self):
        """Test user login endpoint."""
        url = reverse('knox_login')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')
        self.assertEqual(response.data['user']['email'], 'test@example.com')

    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        url = reverse('knox_login')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_logout(self):
        """Test user logout endpoint."""
        instance, token = AuthToken.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        url = reverse('knox_logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify token is deleted
        self.assertFalse(AuthToken.objects.filter(user=self.user, digest=instance.digest).exists())


class UserRegistrationAPITest(APITestCase):
    """Test cases for user registration API."""

    def test_user_registration(self):
        """Test user registration endpoint."""
        url = reverse('user-list')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'password_confirm': 'newpassword123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

        # Verify user was created correctly
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'User')
        self.assertTrue(user.check_password('newpassword123'))

    def test_user_registration_password_mismatch(self):
        """Test registration with mismatched passwords."""
        url = reverse('user-list')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'password_confirm': 'differentpassword',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Passwords do not match', str(response.data))

    def test_user_registration_duplicate_email(self):
        """Test registration with duplicate email."""
        # Create existing user
        User.objects.create_user(
            username='existinguser',
            email='test@example.com',
            password='testpass123'
        )

        url = reverse('user-list')
        data = {
            'username': 'newuser',
            'email': 'test@example.com',  # Duplicate email
            'password': 'newpassword123',
            'password_confirm': 'newpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('A user with this email already exists', str(response.data))

    def test_user_registration_invalid_password(self):
        """Test registration with invalid password."""
        url = reverse('user-list')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': '123',  # Too short
            'password_confirm': '123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfileAPITest(APITestCase):
    """Test cases for user profile API."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )
        self.instance, self.token = AuthToken.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

    def test_get_current_user_profile(self):
        """Test retrieving current user's profile."""
        url = reverse('user-me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertIn('profile', response.data)

    def test_update_current_user_profile(self):
        """Test updating current user's profile."""
        url = reverse('user-me')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com',
            'profile': {
                'bio': 'Updated bio',
                'phone_number': '+1234567890',
                'country': 'US',
                'city': 'New York'
            }
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify user was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.email, 'updated@example.com')

        # Verify profile was updated
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, 'Updated bio')
        self.assertEqual(self.user.profile.phone_number, '+1234567890')
        self.assertEqual(self.user.profile.country, 'US')
        self.assertEqual(self.user.profile.city, 'New York')

    def test_change_password(self):
        """Test changing user password."""
        url = reverse('user-change-password')
        data = {
            'current_password': 'testpass123',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Password changed successfully', response.data['message'])
        self.assertIn('token', response.data)
        self.assertIn('expiry', response.data)

        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))

    def test_change_password_incorrect_current(self):
        """Test changing password with incorrect current password."""
        url = reverse('user-change-password')
        data = {
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Current password is incorrect', str(response.data))

    def test_change_password_mismatch(self):
        """Test changing password with mismatched new passwords."""
        url = reverse('user-change-password')
        data = {
            'current_password': 'testpass123',
            'new_password': 'newpassword123',
            'new_password_confirm': 'differentpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('New passwords do not match', str(response.data))

    def test_get_public_user_profile(self):
        """Test retrieving public user profile."""
        # Make user profile public
        self.user.profile.is_public = True
        self.user.profile.save()

        url = reverse('user-profile', kwargs={'pk': self.user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertIn('profile', response.data)

    def test_get_private_user_profile(self):
        """Test retrieving private user profile returns 404."""
        # Make user profile private
        self.user.profile.is_public = False
        self.user.profile.save()

        url = reverse('user-profile', kwargs={'pk': self.user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_list_shows_only_public_profiles(self):
        """Test that user list only shows users with public profiles."""
        # Create another user with private profile
        private_user = User.objects.create_user(
            username="privateuser",
            email="private@example.com",
            password="testpass123"
        )
        private_user.profile.is_public = False
        private_user.profile.save()

        # Make current user public
        self.user.profile.is_public = True
        self.user.profile.save()

        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['username'], 'testuser')

    def test_unauthorized_access_to_profile_endpoints(self):
        """Test that profile endpoints require authentication."""
        self.client.credentials()  # Remove authentication

        url = reverse('user-me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        url = reverse('user-change-password')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserSearchAndFilterTest(APITestCase):
    """Test cases for user search and filter functionality."""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="john_doe",
            email="john@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe"
        )
        self.user1.profile.is_public = True
        self.user1.profile.save()

        self.user2 = User.objects.create_user(
            username="jane_smith",
            email="jane@example.com",
            password="testpass123",
            first_name="Jane",
            last_name="Smith"
        )
        self.user2.profile.is_public = True
        self.user2.profile.save()

        self.instance, self.token = AuthToken.objects.create(user=self.user1)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

    def test_search_users_by_name(self):
        """Test searching users by first or last name."""
        url = reverse('user-list')

        # Search by first name
        response = self.client.get(url, {'search': 'John'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['first_name'], 'John')

        # Search by last name
        response = self.client.get(url, {'search': 'Smith'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['last_name'], 'Smith')

    def test_search_users_by_username(self):
        """Test searching users by username."""
        url = reverse('user-list')
        response = self.client.get(url, {'search': 'john_doe'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['username'], 'john_doe')

    def test_search_users_by_email(self):
        """Test searching users by email."""
        url = reverse('user-list')
        response = self.client.get(url, {'search': 'jane@example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['email'], 'jane@example.com')

    def test_filter_users_by_active_status(self):
        """Test filtering users by active status."""
        # Deactivate one user
        self.user2.is_active = False
        self.user2.save()

        url = reverse('user-list')
        response = self.client.get(url, {'is_active': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['username'], 'john_doe')

    def test_order_users_by_date_joined(self):
        """Test ordering users by date joined."""
        url = reverse('user-list')
        response = self.client.get(url, {'ordering': 'date_joined'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

        # Should be ordered by date joined (ascending)
        first_user = response.data['results'][0]
        second_user = response.data['results'][1]
        self.assertEqual(first_user['username'], 'john_doe')
        self.assertEqual(second_user['username'], 'jane_smith')
