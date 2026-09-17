from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    
    # Custom user model. Email is the login identifier instead of username.
    
    username = None  # we don't use username at all
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"   # Django ke authentication system mein email ko user's login/identity field samjho
    REQUIRED_FIELDS = []  # email + password are already required by default

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def display_name(self):
        name = self.get_full_name().strip()
        return name or self.email

    @property
    def role_names(self):
        # list of group names this user belongs to
        return list(self.groups.values_list("name", flat=True))