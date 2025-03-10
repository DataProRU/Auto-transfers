from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class CustomUser(AbstractUser):
    ROLES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('user', 'User'),
    )
    role = models.CharField(max_length=10, choices=ROLES, default='user')
    email = models.EmailField(unique=True, null=False, blank=False)
    phone = models.CharField(max_length=15, unique=True, null=False, blank=False)
    telegram = models.CharField(max_length=32, unique=True, null=True, blank=True)
    document_photo = models.ImageField(upload_to='user_documents/', null=False, blank=False)  # Настройте MEDIA_ROOT в settings.py
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    USERNAME_FIELD = 'email'  # Аутентификация по email
    REQUIRED_FIELDS = ['username', 'phone']  # Поля для createsuperuser