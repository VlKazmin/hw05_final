from django.contrib.auth import get_user_model
from django.db import models
from core.models import CreatedModel

User = get_user_model()


class Post(CreatedModel):
    text = models.TextField("Текст поста", help_text="Введите текст поста")
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор",
    )
    group = models.ForeignKey(
        "Group",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="groups",
        verbose_name="Группа",
        help_text="Группа, к которой будет относиться пост",
    )
    image = models.ImageField(
        upload_to="posts/", blank=True, verbose_name="Изображение"
    )

    class Meta:
        ordering = ("-created",)
        verbose_name = "пост"
        verbose_name_plural = "посты"

    def __str__(self):
        return self.text[:15]


class Group(CreatedModel):
    title = models.CharField(max_length=200, verbose_name="Название группы")
    slug = models.SlugField(max_length=20, unique=True)
    description = models.TextField(verbose_name="Описание")

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return self.title


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        help_text="Здесь можно оставить комментарий.",
        related_name="comments",
        verbose_name="Пост",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор",
    )
    text = models.TextField("Текст", help_text="Текст нового комментария")

    class Meta:
        ordering = ("created",)

    def __str__(self):
        return self.text


class Follow(CreatedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="подписчик",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="автор"
    )
