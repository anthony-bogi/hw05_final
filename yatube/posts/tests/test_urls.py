from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы',
        )

        cls.author_user = User.objects.create_user(
            username='author_user')
        cls.another_user = User.objects.create_user(
            username='another_user')

        cls.post = Post.objects.create(
            author=cls.author_user,
            text='Тестовый пост для проверки...',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_post_client = Client()
        self.authorized_post_client.force_login(self.author_user)
        self.authorized_another_client = Client()
        self.authorized_another_client.force_login(self.another_user)
        cache.clear()

    def test_guest_client_urls_status_code(self):
        """Проверка для неавторизованного пользователя."""
        field_urls_code = {
            reverse('posts:index'): HTTPStatus.OK,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): HTTPStatus.OK,
            reverse('posts:group_list',
                    kwargs={'slug': 'not_slug'}): HTTPStatus.NOT_FOUND,
            reverse('posts:profile',
                    kwargs={'username': self.author_user}): HTTPStatus.OK,
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}): HTTPStatus.OK,
            reverse('posts:edit',
                    kwargs={'post_id': self.post.id}): HTTPStatus.FOUND,
            reverse('posts:create'): HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url, response_code in field_urls_code.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, response_code)

    def test_another_user_urls_status_code(self):
        """Проверка для авторизованного пользователя."""
        field_urls_code = {
            reverse('posts:index'): HTTPStatus.OK,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): HTTPStatus.OK,
            reverse('posts:group_list',
                    kwargs={'slug': 'not_slug'}): HTTPStatus.NOT_FOUND,
            reverse('posts:profile',
                    kwargs={'username': self.author_user}): HTTPStatus.OK,
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}): HTTPStatus.OK,
            reverse('posts:edit',
                    kwargs={'post_id': self.post.id}): HTTPStatus.FOUND,
            reverse('posts:create'): HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url, response_code in field_urls_code.items():
            with self.subTest(url=url):
                response = self.authorized_another_client.get(url)
                self.assertEqual(response.status_code, response_code)

    def test_author_user_urls_status_code(self):
        """Проверка для авторизированого автора."""
        field_urls_code = {
            reverse('posts:index'): HTTPStatus.OK,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): HTTPStatus.OK,
            reverse('posts:group_list',
                    kwargs={'slug': 'not_slug'}): HTTPStatus.NOT_FOUND,
            reverse('posts:profile',
                    kwargs={'username': self.author_user}): HTTPStatus.OK,
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}): HTTPStatus.OK,
            reverse('posts:edit',
                    kwargs={'post_id': self.post.id}): HTTPStatus.OK,
            reverse('posts:create'): HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url, response_code in field_urls_code.items():
            with self.subTest(url=url):
                response = self.authorized_post_client.get(url)
                self.assertEqual(response.status_code, response_code)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse(
                'posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.author_user}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}): 'posts/post_detail.html',
            reverse(
                'posts:edit',
                kwargs={'post_id': self.post.id}): 'posts/create_post.html',
            reverse(
                'posts:create'): 'posts/create_post.html',
        }

        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_post_client.get(address)
                self.assertTemplateUsed(response, template)
