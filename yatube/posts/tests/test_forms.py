import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User, Comment

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем пользователя.
        cls.author = User.objects.create_user(username="test__user")

        # Создаем авторизованного пользователя.
        cls.authorized_client = Client()

        # Создаем запись о группе в БД
        cls.group = Group.objects.create(
            title="group_name",
            slug="slug-test",
            description="description_text",
        )

        # Создаем пост и сохраняем в БД по авторством test_author.
        cls.post = Post.objects.create(
            text="test_post",
            author=cls.author,
            group=cls.group,
        )

        # Создаем константы namespace URL адресов.
        cls.PROFILE = reverse(
            "posts:profile", kwargs={"username": f"{cls.author}"}
        )
        cls.POST_CREATE = reverse("posts:post_create")
        cls.POST_EDIT = reverse(
            "posts:post_edit", kwargs={"post_id": f"{cls.post.id}"}
        )
        cls.POST_DETAIL = reverse(
            "posts:post_detail", kwargs={"post_id": f"{cls.post.id}"}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, перемещение изменение папок и файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def setUp(self):
        # Авторизация пользователя
        self.authorized_client.force_login(self.author)

    def test_authorized_client_create_form(self):
        """Проверяем создается ли авторизованным
        пользователем новая запись в БД.
        """
        # Для тестирования загрузки изображений
        # берём байт-последовательность картинки,
        # состоящей из двух пикселей: белого и чёрного
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )

        # Эмулируем файл картинки.
        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )

        # Заполняем форму на странице
        form_date = {
            "text": "test_post_2",
            "group": "",
            "image": uploaded,
        }
        # Подсчитаем количество записей в Post.
        posts_count = Post.objects.count()
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            self.POST_CREATE, data=form_date, follow=True
        )
        # Проверяем что количество постов в БД увеличилось
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, self.PROFILE)

        # Проверяем что пост не присвоен к группе
        self.assertEqual(response.context["page_obj"][0].group, None)

        # Проверяем что запись о создании изображения передалась в БД.
        self.assertTrue(
            Post.objects.filter(
                text="test_post_2",
                group=None,
                image="posts/small.gif",
            ).exists()
        )

    def test_authorized_client_edit_form(self):
        # Создаем новую группу
        self.second_group = Group.objects.create(
            title="group_name_2",
            slug="slug-test_2",
            description="description_text_2",
        )

        form_date = {
            "text": "test_edit_post",
            "group": self.second_group.id,
        }
        response = self.authorized_client.post(
            self.POST_EDIT,
            data=form_date,
            follow=True,
        )
        # Отфильтруем модель Group по заголовку группы second_group
        group_title_test = Group.objects.filter(title="group_name_2").first()

        self.assertEqual(str(response.context["post"]), form_date["text"])
        self.assertEqual(response.context["posts_count"], 1)
        self.assertEqual(str(group_title_test), self.second_group.title)
        self.assertRedirects(response, self.POST_DETAIL)

    def test_anonymous_user_cant_create_post(self):
        """Проверяем что анонимный пользователь не может создать пост."""
        # Количество постов до начала теста.
        posts_count = Post.objects.count()
        form_date = {
            "text": "anonymous_text",
        }
        response = self.client.post(
            self.POST_CREATE,
            data=form_date,
            follow=True,
        )
        self.assertEqual(
            Post.objects.count(),
            posts_count,
            msg="Пост неавторизованного пользователя попал в БД.",
        )
        self.assertFalse(
            response.context["form"].is_valid(),
            msg="Данные не прошли валидацию.",
        )
        self.assertFalse(
            Post.objects.filter(
                text=form_date["text"],
            ).exists()
        )


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username="test__author")
        cls.user = User.objects.create_user(username="test__user")
        cls.author_client = Client()
        cls.authorized_client = Client()

        cls.post = Post.objects.create(
            text="test_post",
            author=cls.author,
            group=None,
        )

        cls.POST_DETAIL = reverse(
            "posts:post_detail", kwargs={"post_id": f"{cls.post.id}"}
        )
        cls.ADD_COMMENT = reverse(
            "posts:add_comment", kwargs={"post_id": f"{cls.post.id}"}
        )

    def setUp(self):
        super().setUp()
        self.author_client.force_login(self.author)
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_guest_cant_add_comment(self):
        """Гость не может оставлять комментарии"""
        form_date = {
            "text": "test_text",
        }
        guest_response = self.client.post(
            self.ADD_COMMENT,
            data=form_date,
            follow=True,
        )
        self.assertRedirects(
            guest_response,
            f"/auth/login/?next=/posts/{self.post.id}/comment/",
        )
        self.assertEqual(Comment.objects.count(), 0)

    def test_auth_user_can_leave_comments(self):
        """Авторизованынй пользователь может оставлять комментарии"""
        form_date = {
            "text": "test_text",
        }
        response = self.authorized_client.post(
            self.ADD_COMMENT,
            data=form_date,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(str(Comment.objects.last()), form_date["text"])
        self.assertRedirects(response, self.POST_DETAIL)

        # Автор может оставлять комментарии
        response = self.author_client.post(
            self.ADD_COMMENT,
            data=form_date,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), 2)
        self.assertEqual(Comment.objects.last().author, self.author)
