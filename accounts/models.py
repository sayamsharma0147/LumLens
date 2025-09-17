from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        PHOTOGRAPHER = "photographer", "Photographer"

    role = models.CharField(
        max_length=20, choices=Roles.choices, default=Roles.CUSTOMER
    )

    def is_customer(self) -> bool:
        return self.role == self.Roles.CUSTOMER

    def is_photographer(self) -> bool:
        return self.role == self.Roles.PHOTOGRAPHER
