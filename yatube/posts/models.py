from django.contrib.auth import get_user_model
from django.db import models

from core.models import CoreModel

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, null=False)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(CoreModel):
    text = models.TextField(verbose_name="Пост", help_text="Введите текст")
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор",
    )
    image = models.ImageField(
        ("Фото"),
        upload_to="posts/",
        blank=True,
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="posts",
        verbose_name="Группа",
        help_text="Выберите группу",
    )

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    text = models.TextField(verbose_name="Оставить комментарий")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created",)

    def __str__(self) -> str:
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        related_name="follower",
        on_delete=models.CASCADE,
        verbose_name="Подписчик",
        blank=True
    )
    author = models.ForeignKey(
        User,
        related_name="following",
        on_delete=models.CASCADE,
        verbose_name="Автор",
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name="unique_subscription")]
