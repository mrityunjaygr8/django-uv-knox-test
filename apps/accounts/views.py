from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView, LogoutView as KnoxLogoutView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import UserProfile
from .serializers import (
    UserSerializer, UserUpdateSerializer, UserProfileSerializer,
    PasswordChangeSerializer, PublicUserSerializer, LoginSerializer
)


class LoginView(KnoxLoginView):
    """
    Knox-based login view that returns user information with token.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)

        response = super(LoginView, self).post(request, format=None)
        token_data = response.data

        # Add user information to the response
        token_data.update({
            'user': {
                'id': user.pk,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        })

        return Response(token_data)


class LogoutView(KnoxLogoutView):
    """
    Knox-based logout view that invalidates the current token.
    """
    permission_classes = (permissions.IsAuthenticated,)


class LogoutAllView(KnoxLogoutView):
    """
    Knox-based logout view that invalidates all tokens for the user.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, format=None):
        AuthToken.objects.filter(user=request.user).delete()
        return Response({'message': 'All tokens invalidated successfully.'}, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users with authentication features.
    """
    queryset = User.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'is_staff']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering_fields = ['username', 'date_joined', 'last_login']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'create':
            return UserSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'list':
            return PublicUserSerializer
        return UserSerializer

    def get_permissions(self):
        """
        Instantiate and return the list of permissions that this view requires.
        """
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'me':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filter queryset based on user permissions.
        """
        if self.action == 'list':
            # For list view, only show public profiles
            return User.objects.filter(
                is_active=True,
                profile__is_public=True
            ).select_related('profile')
        return super().get_queryset()

    def perform_update(self, serializer):
        """
        Only allow users to update their own profile.
        """
        if serializer.instance != self.request.user:
            raise permissions.PermissionDenied("You can only update your own profile.")
        serializer.save()

    def perform_destroy(self, instance):
        """
        Soft delete user by deactivating instead of hard delete.
        """
        if instance != self.request.user:
            raise permissions.PermissionDenied("You can only delete your own account.")
        instance.is_active = False
        instance.save()

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """
        Retrieve or update the current user's profile.
        """
        if request.method == 'GET':
            serializer = UserSerializer(request.user)
            return Response(serializer.data)

        elif request.method in ['PUT', 'PATCH']:
            partial = request.method == 'PATCH'
            serializer = UserUpdateSerializer(
                request.user,
                data=request.data,
                partial=partial
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """
        Change the current user's password.
        """
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            # Invalidate all existing tokens and create a new one
            AuthToken.objects.filter(user=request.user).delete()
            instance, token = AuthToken.objects.create(user=request.user)

            return Response({
                'message': 'Password changed successfully.',
                'token': token,
                'expiry': instance.expiry
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        """
        Logout the current user by deleting their current token.
        """
        request._auth.delete()
        return Response({'message': 'Successfully logged out.'})

    @action(detail=False, methods=['post'])
    def logout_all(self, request):
        """
        Logout the current user from all devices by deleting all tokens.
        """
        AuthToken.objects.filter(user=request.user).delete()
        return Response({'message': 'Successfully logged out from all devices.'})

    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        """
        Get public profile information for a specific user.
        """
        user = self.get_object()
        if not hasattr(user, 'profile') or not user.profile.is_public:
            return Response(
                {'error': 'Profile is not public.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PublicUserSerializer(user)
        return Response(serializer.data)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user profiles directly.
    """
    queryset = UserProfile.objects.filter(is_deleted=False)
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Users can only access their own profile.
        """
        return UserProfile.objects.filter(
            user=self.request.user,
            is_deleted=False
        )

    def perform_update(self, serializer):
        """
        Ensure users can only update their own profile.
        """
        if serializer.instance.user != self.request.user:
            raise permissions.PermissionDenied("You can only update your own profile.")
        serializer.save()
