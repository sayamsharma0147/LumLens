from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import uuid


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Roles(models.TextChoices):
        CUSTOMER = 'customer', 'Customer'
        PHOTOGRAPHER = 'photographer', 'Photographer'

    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    displayName = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=20, choices=Roles.choices)
    createdAt = models.DateTimeField(auto_now_add=True)

    username = models.CharField(max_length=150, blank=True, default='', unique=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self) -> str:
        return f"{self.email} ({self.role})"


class PhotographerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='photographer_profile')
    bio = models.TextField(blank=True)
    profile_image = models.URLField(blank=True, help_text="URL to profile image")
    availableForBooking = models.BooleanField(default=True)
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Photographer Profile"
        verbose_name_plural = "Photographer Profiles"

    def __str__(self) -> str:
        return f"Profile for {self.user.email}"

    def save(self, *args, **kwargs):
        # Ensure user role is photographer
        if self.user.role != User.Roles.PHOTOGRAPHER:
            raise ValueError("User must have photographer role to create PhotographerProfile")
        super().save(*args, **kwargs)


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        COMPLETED = 'completed', 'Completed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_bookings')
    photographer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photographer_bookings')
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-createdAt']

    def clean(self):
        # Enforce correct roles at the model level
        if self.customer.role != User.Roles.CUSTOMER:
            raise ValueError('customer must have role=customer')
        if self.photographer.role != User.Roles.PHOTOGRAPHER:
            raise ValueError('photographer must have role=photographer')

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Booking {self.id} {self.customer.email} -> {self.photographer.email} on {self.date} {self.time} [{self.status}]"
