import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User

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

        # Создаем байт-последовательность картинки,
        # состоящей из двух пикселей: белого и чёрного.
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )

        # Эмулируем файл картинки.
        cls.uploaded = SimpleUploadedFile(
            name="small.gif", content=cls.small_gif, content_type="image/gif"
        )

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
            image=cls.uploaded,
        )

        # Создаем константы namespace URL адресов.
        cls.INDEX = reverse("posts:index")
        cls.GROUP_LIST = reverse(
            "posts:group_list", kwargs={"slug": "slug-test"}
        )
        cls.PROFILE = reverse(
            "posts:profile", kwargs={"username": f"{cls.author}"}
        )
        cls.POST_DETAIL = reverse(
            "posts:post_detail", kwargs={"post_id": f"{cls.post.id}"}
        )
        cls.POST_CREATE = reverse("posts:post_create")
        cls.POST_EDIT = reverse(
            "posts:post_edit", kwargs={"post_id": f"{cls.post.id}"}
        )

    @classmethod
    def tearDownClass(cls):
        """Удаление временной директорию и всего его содержимого."""
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Авторизация пользователя
        self.authorized_client.force_login(self.author)
        cache.clear()

    def post_contex_is_valid_check(self, url):
        """Вызываемая функция проверки передачи данных в context по ключам
        [page_obj] или [post] модели Post.
        """
        response = self.authorized_client.get(url)

        if "page_obj" in response.context:
            first_object = response.context["page_obj"][0]
        else:
            first_object = response.context["post"]

        self.assertIsInstance(first_object, Post)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(first_object.image, self.post.image)

        return response

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        self.post_contex_is_valid_check(self.INDEX)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.post_contex_is_valid_check(self.GROUP_LIST)
        group = response.context["group"]

        self.assertIsInstance(group, Group)
        self.assertEqual(group, self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.post_contex_is_valid_check(self.PROFILE)

        author = response.context["author"]
        self.assertIsInstance(author, User)
        self.assertEqual(author, self.author)

        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj), 1)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.post_contex_is_valid_check(self.POST_DETAIL)

        post = response.context["post"]
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.id, self.post.id)
        self.assertIsInstance(post, Post)

        posts_count = response.context["posts_count"]
        self.assertEqual(posts_count, 1)

    def post_form_contex_is_valid_check(self, url):
        """Вызываемая функция проверки передачи данных в context
        в форму PostForm модели Post.
        """
        response = self.authorized_client.get(url)
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
            "image": forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)
        return response

    def test_post_create_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        self.post_form_contex_is_valid_check(self.POST_CREATE)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.post_form_contex_is_valid_check(self.POST_EDIT)

        is_edit = response.context["is_edit"]
        self.assertTrue(is_edit)

    def test_post_falls_into_the_correct_group(self):
        """Пост относится к присвоенной группе и отображается на
        главной странице, в пофиле автора и выбранной группе.
        Не попал в группу, для которой не был предназначен.
        """
        # Создаем новую группу.
        self.group_2 = Group.objects.create(
            title="group_name_2",
            slug="slug-test_2",
            description="description_text_2",
        )
        # Создаем пост в новой группе.
        self.post_2 = Post.objects.create(
            text="test_post_2",
            author=self.author,
            group=self.group_2,
        )
        # Проверяем что пост отображается на главной странице,
        # относится к новой группе под правильным авторством.
        response = self.authorized_client.get(self.INDEX)
        post = response.context["page_obj"][0]
        with self.subTest(post=post):
            self.assertIsInstance(post, Post)
            self.assertEqual(post.author, self.author)
            self.assertEqual(post.group, self.group_2)
            # Проверяем, что этот пост не попал в группу,
            # для которой не был предназначен
            self.assertNotEqual(post.group, self.group)

        # Проверяем что на странице выбранной группы отоброжается
        # новый пост.
        response_2 = self.authorized_client.get(
            reverse("posts:group_list", kwargs={"slug": "slug-test_2"})
        )
        group = response_2.context["group"]
        post = response_2.context["posts"][0]
        with self.subTest(post=post, group=group):
            self.assertIsInstance(group, Group)
            self.assertEqual(group, self.group_2)
            self.assertEqual(post, self.post_2)

        # Проверяем наличие нового поста в профайле пользователя
        response_3 = self.authorized_client.get(self.PROFILE)
        post = response_3.context["page_obj"][:]
        with self.subTest(post=post):
            self.assertEqual(len(post), 2)

    def test_index_page_cache(self):
        """Тестируем работу кэширования index.html"""
        new_post = Post.objects.create(
            text="test_post_2",
            author=self.author,
            group=self.group,
        )
        response = len(self.authorized_client.get(self.INDEX).content)
        new_post.delete()
        response_after_del_post = len(
            self.authorized_client.get(self.INDEX).content
        )
        self.assertEqual(response, response_after_del_post)
        cache.clear()
        response_after_clean_cache = len(
            self.authorized_client.get(self.INDEX).content
        )
        self.assertNotEqual(response, response_after_clean_cache)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.NUM_OF_POSTS_CREATE: int = 13
        cls.PAGINATE_BY: int = 10

        cls.author = User.objects.create_user(username="author")
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)

        cls.group = Group.objects.create(
            title="group_name",
            slug="slug-test",
            description="description_text",
        )

        # Создаем словарь namespace: URL адрес.
        cls.list_url_reverse_template = {
            "INDEX": reverse("posts:index"),
            "GROUP_LIST": reverse(
                "posts:group_list", kwargs={"slug": "slug-test"}
            ),
            "PROFILE": reverse(
                "posts:profile", kwargs={"username": f"{cls.author}"}
            ),
        }
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """Проверяем, что количество постов
        на первой странице равно 10, а на второй - 3"""
        # Здесь создаются фикстуры: клиент и 13 тестовых записей.
        Post.objects.bulk_create(
            Post(
                text=f"test_post_{num}",
                author=self.author,
                group=self.group,
            )
            for num in range(self.NUM_OF_POSTS_CREATE)
        )
        for url in self.list_url_reverse_template.values():
            with self.subTest(url=url):
                posts_on_second_page: int = 3

                # Проверка: количество постов на первой странице равно 10.
                response = self.authorized_client.get(url)
                self.assertEqual(
                    len(response.context["page_obj"]), self.PAGINATE_BY
                )

                # Проверка: на второй странице должно быть три поста.
                response_2 = self.authorized_client.get(url + "?page=2")
                self.assertEqual(
                    len(response_2.context["page_obj"]), posts_on_second_page
                )


class FollowViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем автора поста.
        cls.author = User.objects.create_user(username="post_author")
        cls.author_client = Client()

        # Создаем пользователя.
        cls.user = User.objects.create_user(username="auth_user")
        cls.user_client = Client()

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
        cls.FOLLOW = reverse("posts:follow_index")
        cls.PROFILE_FOLLOW = reverse(
            "posts:profile_follow", kwargs={"username": f"{cls.author}"}
        )
        cls.PROFILE_UNFOLLOW = reverse(
            "posts:profile_unfollow", kwargs={"username": f"{cls.author}"}
        )

    def setUp(self):
        # Авторизация пользователей
        self.author_client.force_login(self.author)
        self.user_client.force_login(self.user)
        cache.clear()

    def test_authorized_user_follow_author(self):
        """Проверяем что авторизованный пользователь
        может подписываться на авторов
        """
        follow_test_data = {
            "follower_count": 1,
            "follower_name": self.user,
            "post_author": self.author,
            "redirect": self.PROFILE,
        }
        response = self.user_client.post(
            self.PROFILE_FOLLOW,
        )
        for value in follow_test_data.values():
            with self.subTest(value=value):
                # Проверяем что количество подписчиков увеличилось
                self.assertEqual(
                    Follow.objects.count(), follow_test_data["follower_count"]
                )
                # Проверяем имя последнего подписавшегося пользователя
                self.assertEqual(
                    Follow.objects.last().user,
                    follow_test_data["follower_name"],
                )
                # Проверяем имя автора, на которого подписался клиет
                self.assertEqual(
                    Follow.objects.last().author,
                    follow_test_data["post_author"],
                )
                # Верный редирект
                self.assertRedirects(response, follow_test_data["redirect"])

    def test_authorized_user_unfollow_author(self):
        """Проверяем что авторизованный пользователь
        может отписываться от авторов
        """
        unfollow_test_data = {
            "follower_count": 0,
            "redirect": self.PROFILE,
        }
        response = self.user_client.post(
            self.PROFILE_UNFOLLOW,
        )
        for value in unfollow_test_data.values():
            with self.subTest(value=value):
                # Проверяем что количество подписчиков уменьшилось
                self.assertEqual(
                    Follow.objects.count(),
                    unfollow_test_data["follower_count"],
                )
                # Верный редирект
                self.assertRedirects(response, unfollow_test_data["redirect"])

    def test_follow_page_for_authorized_user(self):
        """ Проверяем что новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан.
        """
        # Подписываемся на автора
        follow = Follow.objects.create(
            user=self.user,
            author=self.author,
        )
        response = self.user_client.get(self.FOLLOW)
        self.assertContains(response, text=self.post, count=1, status_code=200)

        # Отписываемся от автора
        follow.delete()
        self.assertContains(response, text=None, count=0, status_code=200)

    def test_non_authorized_user_cant_follow_author(self):
        """Проверяем что гость не может подписаться на автора"""
        response = self.client.post(self.PROFILE_FOLLOW)
        redirect_path = f"/auth/login/?next=/profile/{self.author}/follow/"
        self.assertRedirects(response, redirect_path)
