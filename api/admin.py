from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import PhotographerProfile


User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('uid', 'email', 'displayName', 'role', 'is_active', 'is_staff', 'date_joined', 'createdAt')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('email', 'displayName')


@admin.register(PhotographerProfile)
class PhotographerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'availableForBooking', 'createdAt')
    list_filter = ('availableForBooking', 'createdAt')
    search_fields = ('user__email', 'user__displayName', 'bio')
    readonly_fields = ('createdAt',)

# Register your models here.
