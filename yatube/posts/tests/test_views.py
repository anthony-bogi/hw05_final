from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Follow, Group, Post

User = get_user_model()


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Anthony')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для проверки...',
            group=cls.group,
            image=uploaded,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def posts_check_all_fields(self, post):
        """Метод для проверки поля поста."""
        with self.subTest(post=post):
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.group.id, self.post.group.id)
            self.assertEqual(post.image, self.post.image)

    def test_posts_context_index_template(self):
        """
        Формирование шаблона index с правильным контекстом.
        Появление поста при создании на главной странице.
        """
        response = self.authorized_client.get(reverse('posts:index'))
        self.posts_check_all_fields(response.context['page_obj'][0])
        last_post = response.context['page_obj'][0]
        self.assertEqual(last_post, self.post)

    def test_posts_context_group_list_template(self):
        """
        Формирование шаблона group_list с правильным контекстом.
        Появление поста при создании на странице его группы.
        """
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug},
            )
        )
        test_group = response.context['group']
        self.posts_check_all_fields(response.context['page_obj'][0])
        test_post = str(response.context['page_obj'][0])
        self.assertEqual(test_group, self.group)
        self.assertEqual(test_post, str(self.post))

    def test_posts_context_post_create_template(self):
        """Формирование шаблона post_create с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:create'))

        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_posts_context_post_edit_template(self):
        """Формирование шаблона post_edit с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:edit',
                kwargs={'post_id': self.post.id},
            )
        )

        form_fields = {'text': forms.fields.CharField}

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_posts_context_profile_template(self):
        """Формирование шаблона profile с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username},
            )
        )

        self.posts_check_all_fields(response.context['page_obj'][0])
        self.assertEqual(response.context['author'], self.user)

    def test_posts_context_post_detail_template(self):
        """Формирование шаблона post_detail с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id},
            )
        )

        self.posts_check_all_fields(response.context['post'])

    def test_posts_not_from_foreign_group(self):
        """Не попадание поста в другую группу."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.posts_check_all_fields(response.context['page_obj'][0])
        post = response.context['page_obj'][0]
        group = post.group
        self.assertEqual(group, self.group)

    def test_cache_index_page(self):
        """Проверка работы кеша."""
        post = Post.objects.create(
            text='Пост для кеш',
            author=self.user)
        content_add = self.authorized_client.get(
            reverse('posts:index')).content
        post.delete()
        content_delete = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertEqual(content_add, content_delete)
        cache.clear()
        content_cache_clear = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertNotEqual(content_add, content_cache_clear)


class PostsPaginatorViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Anthony')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        for count in range(13):
            cls.post = Post.objects.create(
                text=f'Тестовый текст поста {count}',
                author=cls.user,
            )

    def setUp(self):
        cache.clear()

    def test_posts_if_first_page_has_ten_records(self):
        """Проверка: количество постов на первой странице равно 10."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context.get('page_obj').object_list), 10)

    def test_posts_if_second_page_has_three_records(self):
        """Проверка: на второй странице должно быть три поста."""
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(len(response.context.get('page_obj').object_list), 3)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_author = User.objects.create(
            username='post_author',
        )
        cls.post_follower = User.objects.create(
            username='post_follower',
        )
        cls.post = Post.objects.create(
            text='Подписывайся на мой канал',
            author=cls.post_author,
        )

    def setUp(self):
        cache.clear()
        self.author_client = Client()
        self.author_client.force_login(self.post_author)
        self.follower_client = Client()
        self.follower_client.force_login(self.post_follower)

    def test_follow_on_user(self):
        """Подписка на пользователя."""
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.post_author}
            )
        )
        follow = Follow.objects.all().latest('id')
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author_id, self.post_author.id)
        self.assertEqual(follow.user_id, self.post_follower.id)

    def test_unfollow_on_user(self):
        """Отписка от пользователя."""
        Follow.objects.create(
            user=self.post_follower,
            author=self.post_author
        )
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.post_author}
            )
        )
        self.assertEqual(Follow.objects.count(), count_follow - 1)

    def test_follow_on_authors(self):
        """Проверка записей у тех, кто подписан."""
        post = Post.objects.create(
            author=self.post_author,
            text="Подписывайся на мой канал"
        )
        Follow.objects.create(
            user=self.post_follower,
            author=self.post_author
        )
        response = self.follower_client.get(
            reverse('posts:follow_index')
        )
        self.assertIn(post, response.context['page_obj'].object_list)

    def test_notfollow_on_authors(self):
        """Проверка записей у тех кто, не подписан."""
        post = Post.objects.create(
            author=self.post_author,
            text="Подписывайся на мой канал"
        )
        response = self.follower_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(post, response.context['page_obj'].object_list)
