from django.contrib.auth.models import AbstractUser
from django.db import models

MAX_MEASUREMENT_LENGTH = 20
MAX_NAME_LENGTH = 64


class FoodgramUser(AbstractUser):
    avatar = models.ImageField(
        upload_to='api/images/', null=True, default=None
    )
    is_subscribed = models.ManyToManyField(
        'self', symmetrical=False, blank=True, related_name='subscribers'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return self.username