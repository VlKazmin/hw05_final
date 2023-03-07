from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим тестового пользователя
        cls.user = User.objects.create_user(username="NoName")
        # Создадим запись в БД для проверки slug
        cls.group = Group.objects.create(
            title="group_test",
            slug="slug-test",
            description="description_text",
        )
        # Создадим пост для проверки вызываемых шаблонов
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовое описание" * 3,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__, которая
        выводит первые 15 символов."""
        post = PostModelTest.post
        self.assertEqual(post.text[:15], str(post))

    def test_models_have_correct_group_names(self):
        """Проверяем, корректное отображение название группы"""
        group = PostModelTest.group.title
        self.assertEqual(group, str(group))

    def test_verbose_name(self):
        post = PostModelTest.post
        field_verboses = {
            "text": "Текст поста",
            "created": "Дата публикации",
            "author": "Автор",
            "group": "Группа",
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_help_text(self):
        post = PostModelTest.post
        field_help_texts = {
            "text": "Введите текст поста",
            "group": "Группа, к которой будет относиться пост",
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )
