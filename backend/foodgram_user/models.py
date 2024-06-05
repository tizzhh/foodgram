from django.contrib.auth.models import AbstractUser
from django.db import models

MAX_MEASUREMENT_LENGTH = 20
MAX_NAME_LENGTH = 64


class FoodgramUser(AbstractUser):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    avatar = models.ImageField(
        upload_to='api/images/', null=True, default=None
    )
    is_subscribed = models.ManyToManyField(
        'self', symmetrical=False, blank=True, related_name='subscribers'
    )
    email = models.EmailField(unique=True)

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return self.username
