from rest_framework import serializers
from accounts.models.user import CustomUser
from django.core.validators import RegexValidator


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)  # Пароль не возвращается в ответе
    phone = serializers.CharField(
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Номер телефона должен быть в формате: '+79991234567'."
            )
        ]
    )
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'phone', 'telegram', 'document_photo', 'password')

    def create(self, validated_data):
        # Создание пользователя с хешированным паролем
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],  # Пароль хешируется автоматически
            username=validated_data['username'],
            phone=validated_data['phone'],
            telegram=validated_data['telegram'],
            document_photo=validated_data['document_photo']
        )
        return user


