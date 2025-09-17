from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Booking, Notification, PhotographerProfile
from .serializers import (
    BookingCreateSerializer,
    BookingSerializer,
    BookingStatusUpdateSerializer,
    NotificationSerializer,
    PhotographerListSerializer,
    PhotographerProfileSerializer,
    PhotographerUpdateSerializer,
    SignupSerializer,
    UserSerializer,
)

User = get_user_model()


class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    @staticmethod
    def get(request):
        return Response(UserSerializer(request.user).data)


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.EMAIL_FIELD

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        token["displayName"] = user.displayName
        return token

    def validate(self, attrs):
        # Map email/password to parent serializer's username/password
        email = (
            attrs.get("email") if "email" in attrs else self.initial_data.get("email")
        )
        if email:
            attrs["username"] = email
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class LoginView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


class AuthTestView(APIView):
    permission_classes = [permissions.AllowAny]

    @staticmethod
    def get(request):
        if request.user.is_authenticated:
            payload = None
            try:
                # SimpleJWT attaches a validated token to request.auth
                if request.auth:
                    payload = dict(request.auth)
            except Exception:
                payload = None
            return Response(
                {
                    "authenticated": True,
                    "user": UserSerializer(request.user).data,
                    "jwt": payload,
                }
            )
        return Response({"authenticated": False})


class PhotographerListView(generics.ListAPIView):
    """
    List all photographers available for booking.
    Public endpoint - no authentication required.
    """

    serializer_class = PhotographerListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return PhotographerProfile.objects.filter(
            availableForBooking=True
        ).select_related("user")


class PhotographerDetailView(generics.RetrieveAPIView):
    """
    Get single photographer profile by user ID.
    Public endpoint - no authentication required.
    """

    serializer_class = PhotographerProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        user_id = self.kwargs.get("id")
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
            raise PermissionDenied(
                "Only photographers can update their profile"
            )

        profile, _ = PhotographerProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"bio": "", "profile_image": "", "availableForBooking": True},
        )
        return profile

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PhotographerProfileSerializer
        return PhotographerUpdateSerializer


class PhotographersTestView(APIView):
    permission_classes = [permissions.AllowAny]

    @staticmethod
    def get(request):
        count = PhotographerProfile.objects.filter(availableForBooking=True).count()
        return Response({"available_photographers": count})


class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.role != User.Roles.CUSTOMER:
            raise PermissionDenied("Only customers can create bookings")
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        booking = serializer.instance
        # Notify photographer of new booking request
        Notification.objects.create(
            user=booking.photographer,
            booking=booking,
            message="New booking request",
        )
        output = BookingSerializer(booking).data
        return Response(output, status=201)


class BookingMeListView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Roles.CUSTOMER:
            return Booking.objects.filter(customer=user).select_related(
                "customer", "photographer"
            )
        elif user.role == User.Roles.PHOTOGRAPHER:
            return Booking.objects.filter(photographer=user).select_related(
                "customer", "photographer"
            )
        return Booking.objects.none()


class BookingsTestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def get(request):
        user = request.user
        if user.role == User.Roles.CUSTOMER:
            count = Booking.objects.filter(customer=user).count()
        elif user.role == User.Roles.PHOTOGRAPHER:
            count = Booking.objects.filter(photographer=user).count()
        else:
            count = 0
        return Response({"bookings_count": count})


class BookingStatusUpdateView(generics.UpdateAPIView):
    serializer_class = BookingStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Booking.objects.all()
    lookup_field = "id"

    def get_object(self):
        booking = get_object_or_404(Booking, id=self.kwargs["id"])
        if (
            self.request.user.role != User.Roles.PHOTOGRAPHER
            or booking.photographer != self.request.user
        ):
            raise PermissionDenied(
                "Only the assigned photographer can update this booking"
            )
        return booking

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        booking = self.get_object()
        Notification.objects.create(
            user=booking.customer,
            booking=booking,
            message=f"Booking {booking.status}",
        )
        return response


class BookingCompleteView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()
    lookup_field = "id"

    def update(self, request, *args, **kwargs):
        booking = self.get_object()
        if (
            request.user.role != User.Roles.PHOTOGRAPHER
            or booking.photographer != request.user
        ):
            raise PermissionDenied(
                "Only the assigned photographer can complete this booking"
            )
        booking.status = Booking.Status.COMPLETED
        booking.save()
        # Notify customer of completion
        Notification.objects.create(
            user=booking.customer,
            booking=booking,
            message="Booking completed",
        )
        serializer = BookingSerializer(booking)
        return Response(serializer.data)


class NotificationMeListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class NotificationMarkReadView(generics.UpdateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        # Only allow updates to own notifications
        return Notification.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response(NotificationSerializer(notification).data)
