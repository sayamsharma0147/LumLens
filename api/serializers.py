from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import PhotographerProfile, Booking, Notification


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['uid', 'email', 'displayName', 'role', 'date_joined', 'createdAt']
        read_only_fields = ['uid', 'date_joined', 'createdAt']


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'displayName', 'role']

    @staticmethod
    def validate_password(value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class EmailTokenObtainSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(request=self.context.get('request'), email=email, password=password)
        if not user:
            raise serializers.ValidationError('Invalid credentials')
        attrs['user'] = user
        return attrs


class PhotographerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = PhotographerProfile
        fields = ['user', 'bio', 'profile_image', 'availableForBooking', 'createdAt']
        read_only_fields = ['createdAt']


class PhotographerListSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = PhotographerProfile
        fields = ['user', 'bio', 'profile_image', 'availableForBooking']


class PhotographerUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotographerProfile
        fields = ['bio', 'profile_image', 'availableForBooking']


class BookingSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.displayName', read_only=True)
    photographer_name = serializers.CharField(source='photographer.displayName', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'customer', 'photographer', 'customer_name', 'photographer_name',
            'date', 'time', 'status', 'createdAt'
        ]
        read_only_fields = ['id', 'status', 'createdAt', 'customer']


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['photographer', 'date', 'time']

    @staticmethod
    def validate_photographer(value):
        if value.role != User.Roles.PHOTOGRAPHER:
            raise serializers.ValidationError('Selected user is not a photographer')
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        if user.role != User.Roles.CUSTOMER:
            raise serializers.ValidationError('Only customers can create bookings')
        return Booking.objects.create(customer=user, **validated_data)


class BookingStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['status']
        extra_kwargs = {
            'status': {'required': True}
        }

    @staticmethod
    def validate_status(value):
        allowed = {Booking.Status.ACCEPTED, Booking.Status.REJECTED}
        if value not in allowed:
            raise serializers.ValidationError('Status must be accepted or rejected')
        return value


class NotificationSerializer(serializers.ModelSerializer):
    booking = serializers.UUIDField(source='booking.id', allow_null=True, read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'booking', 'message', 'is_read', 'createdAt']
        read_only_fields = ['id', 'booking', 'message', 'createdAt']
