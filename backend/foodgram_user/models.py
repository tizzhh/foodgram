from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F, Q

from foodgram_user.constants import MAX_NAME_LENGTH


class FoodgramUser(AbstractUser):
    first_name = models.CharField(max_length=MAX_NAME_LENGTH)
    last_name = models.CharField(max_length=MAX_NAME_LENGTH)
    avatar = models.ImageField(
        upload_to='api/images/', null=True, default=None
    )
    is_subscribed = models.ManyToManyField(
        'self', symmetrical=False, blank=True, related_name='subscribers'
    )
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('last_name', 'first_name', 'username')

    class Meta:
        ordering = ('email',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return self.username


class Subscribe(models.Model):
    user = models.ForeignKey(
        FoodgramUser, related_name='subscription', on_delete=models.CASCADE
    )
    subscription = models.ForeignKey(FoodgramUser, on_delete=models.CASCADE)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'subscription'),
                name='unique_user_subscription',
            ),
            models.CheckConstraint(
                check=~Q(user=F('subscription')),
                name='cannot_subscribe_to_oneself',
            ),
        )
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'

    def __str__(self) -> str:
        return f'{self.user.email} is subscribed to {self.subscribed.email}'
