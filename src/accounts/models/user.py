from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', "Номер в формате: '+79991234567'.")],
        unique=True
    )
    telegram = models.CharField(max_length=32, unique=True)
    document_photo = models.ImageField(upload_to='user_documents/')  # Настройте MEDIA_ROOT в settings.py
    first_name = models.CharField(max_length=30)  # Переопределяем стандартные поля, если нужно
    last_name = models.CharField(max_length=30)

    USERNAME_FIELD = 'email'  # Аутентификация по email
    REQUIRED_FIELDS = ['username', 'phone']  # Поля для createsuperuser
