from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post, User


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем пользователя test_author и логинимся под ним.
        cls.author = User.objects.create_user(username="test_author")
        cls.authorized_author = Client()

        # Создаем авторизованного пользователя.
        cls.user = User.objects.create_user(username="test_user")
        cls.authorized_client = Client()

        # Создаем запись о группе в БД
        cls.group = Group.objects.create(
            title="group_test",
            slug="slug-test",
            description="description_text",
        )

        # Создаем пост и сохраняем в БД по авторством test_author.
        cls.post = Post.objects.create(
            text="test_post",
            author=cls.author,
        )
        # Создаем константы path URL адресов.
        cls.INDEX = "/"
        cls.GROUP_LIST = f"/group/{cls.group.slug}/"
        cls.PROFILE = f"/profile/{cls.author.username}/"
        cls.POST_DETAIL = f"/posts/{cls.post.id}/"
        cls.POST_CREATE = "/create/"
        cls.POST_EDIT = f"/posts/{cls.post.id}/edit/"
        cls.POST_CREATE_REDIRECTS = "/auth/login/?next=/create/"
        cls.POST_EDIT_REDIRECTS = (
            "/auth/" f"login/?next=/posts/{cls.post.id}/edit/"
        )
        cls.FAKE_PAGE = "/fake_page/"
        cls.FOLLOW_INDEX = "/follow/"
        cls.PROFILE_FOLLOW = f"/profile/{cls.author.username}/"
        cls.PROFILE_UNFOLLOW = f"/profile/{cls.author.username}/"

        # Создаем список общедоступных URL.
        cls.public_urls = (
            (cls.INDEX, "posts/index.html", HTTPStatus.OK),
            (cls.GROUP_LIST, "posts/group_list.html", HTTPStatus.OK),
            (cls.PROFILE, "posts/profile.html", HTTPStatus.OK),
            (cls.POST_DETAIL, "posts/post_detail.html", HTTPStatus.OK),
            (cls.FAKE_PAGE, "/fake_page/", HTTPStatus.NOT_FOUND),
        )

        # Создаем список приватных URL.
        cls.private_urls = [
            (cls.POST_CREATE, "posts/create_post.html", HTTPStatus.OK),
            (cls.POST_EDIT, "posts/create_post.html", HTTPStatus.OK),
            (cls.FOLLOW_INDEX, "posts/follow.html", HTTPStatus.OK),
            (cls.PROFILE_FOLLOW, "posts/profile.html", HTTPStatus.OK),
            (cls.PROFILE_UNFOLLOW, "posts/profile.html", HTTPStatus.OK),
        ]

    def setUp(self):
        # Авторизация пользователей
        self.authorized_author.force_login(self.author)
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template, stat in self.public_urls + tuple(self.private_urls):
            with self.subTest(url=url):
                if url == self.FAKE_PAGE:
                    continue
                response = self.authorized_author.get(url)
                self.assertTemplateUsed(response, template)

    def test_public_url_exists_at_desired_location(self):
        """Проверяем общедоступные страницы для неавторизованного
        пользователя.
        """
        for url, template, status in self.public_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, status)

    def test_private_url_for_author_post(self):
        """Проверяем приватные страницы для авторизованного пользователя
        и автора поста.
        """
        for url, template, status in self.private_urls:
            with self.subTest(url=url):
                response = self.authorized_author.get(url)
                self.assertEqual(response.status_code, status)

    def test_private_url_for_authorized_client(self):
        """Проверяем приватные страницы для авторизованного пользователя"""
        templates_url_names = {
            self.POST_CREATE: HTTPStatus.OK,
            self.POST_EDIT: HTTPStatus.FOUND,
            self.FOLLOW_INDEX: HTTPStatus.OK,
            self.PROFILE_FOLLOW: HTTPStatus.OK,
            self.PROFILE_UNFOLLOW: HTTPStatus.OK,
        }
        for url, status in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, status)

    def test_task_list_url_redirect_anonymous_on_admin_login(self):
        """Проверяем редиректы для неавторизованного пользователя."""
        templates_url_names = {
            self.POST_CREATE: self.POST_CREATE_REDIRECTS,
            self.POST_EDIT: self.POST_EDIT_REDIRECTS,
        }

        for url, url_path in templates_url_names.items():
            self.subTest(url=url)
            response = self.client.get(url, follow=True)
            self.assertRedirects(response, url_path)

    def test_url_redirect_authorized_client_on_post_detail(self):
        """Проверяем редирект для авторизованного пользователя,
        не являющимся автором поста.
        """
        templates_url_names = {
            self.POST_EDIT: self.POST_DETAIL,
        }

        for url, url_path in templates_url_names.items():
            self.subTest(url=url)
            response = self.authorized_client.get(url, follow=True)
            self.assertRedirects(response, url_path)
