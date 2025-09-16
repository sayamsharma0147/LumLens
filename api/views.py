from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import PhotographerProfile, Booking
from .serializers import (
    SignupSerializer, UserSerializer, EmailTokenObtainSerializer,
    PhotographerProfileSerializer, PhotographerListSerializer, PhotographerUpdateSerializer,
    BookingSerializer, BookingCreateSerializer, BookingStatusUpdateSerializer
)


User = get_user_model()


class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.EMAIL_FIELD

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['email'] = user.email
        token['displayName'] = user.displayName
        return token

    def validate(self, attrs):
        # Map email/password to parent serializer's username/password
        email = attrs.get('email') if 'email' in attrs else self.initial_data.get('email')
        if email:
            attrs['username'] = email
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data


class LoginView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


class AuthTestView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            payload = None
            try:
                # SimpleJWT attaches a validated token to request.auth
                if request.auth:
                    payload = dict(request.auth)
            except Exception:
                payload = None
            return Response({
                'authenticated': True,
                'user': UserSerializer(request.user).data,
                'jwt': payload,
            })
        return Response({'authenticated': False})


class PhotographerListView(generics.ListAPIView):
    """
    List all photographers available for booking.
    Public endpoint - no authentication required.
    """
    serializer_class = PhotographerListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return PhotographerProfile.objects.filter(availableForBooking=True).select_related('user')


class PhotographerDetailView(generics.RetrieveAPIView):
    """
    Get single photographer profile by user ID.
    Public endpoint - no authentication required.
    """
    serializer_class = PhotographerProfileSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_object(self):
        user_id = self.kwargs.get('id')
        return get_object_or_404(PhotographerProfile, user__uid=user_id)


class PhotographerUpdateView(generics.RetrieveUpdateAPIView):
    """
    Update logged-in photographer's profile.
    Requires authentication and photographer role.
    """
    serializer_class = PhotographerUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        if not self.request.user.is_photographer():
            raise permissions.PermissionDenied("Only photographers can update their profile")
        
        profile, created = PhotographerProfile.objects.get_or_create(
            user=self.request.user,
            defaults={'bio': '', 'profile_image': '', 'availableForBooking': True}
        )
        return profile
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PhotographerProfileSerializer
        return PhotographerUpdateSerializer


class PhotographersTestView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        count = PhotographerProfile.objects.filter(availableForBooking=True).count()
        return Response({'available_photographers': count})


class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        if self.request.user.role != User.Roles.CUSTOMER:
            raise permissions.PermissionDenied('Only customers can create bookings')
        serializer.save()


class BookingMeListView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Roles.CUSTOMER:
            return Booking.objects.filter(customer=user).select_related('customer', 'photographer')
        elif user.role == User.Roles.PHOTOGRAPHER:
            return Booking.objects.filter(photographer=user).select_related('customer', 'photographer')
        return Booking.objects.none()


class BookingsTestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == User.Roles.CUSTOMER:
            count = Booking.objects.filter(customer=user).count()
        elif user.role == User.Roles.PHOTOGRAPHER:
            count = Booking.objects.filter(photographer=user).count()
        else:
            count = 0
        return Response({'bookings_count': count})


class BookingStatusUpdateView(generics.UpdateAPIView):
    serializer_class = BookingStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Booking.objects.all()
    lookup_field = 'id'

    def get_object(self):
        booking = get_object_or_404(Booking, id=self.kwargs['id'])
        if self.request.user.role != User.Roles.PHOTOGRAPHER or booking.photographer != self.request.user:
            raise permissions.PermissionDenied('Only the assigned photographer can update this booking')
        return booking


class BookingCompleteView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()
    lookup_field = 'id'

    def update(self, request, *args, **kwargs):
        booking = self.get_object()
        if request.user.role != User.Roles.PHOTOGRAPHER or booking.photographer != request.user:
            raise permissions.PermissionDenied('Only the assigned photographer can complete this booking')
        booking.status = Booking.Status.COMPLETED
        booking.save()
        serializer = BookingSerializer(booking)
        return Response(serializer.data)
