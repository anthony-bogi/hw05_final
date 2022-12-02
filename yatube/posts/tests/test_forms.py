import tempfile
import shutil

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from http import HTTPStatus

from posts.forms import PostForm
from posts.models import Group, Post, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Anthony')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для проверки...',
            group=cls.group,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_user = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_posts_forms_create_post(self):
        """
        Создание формы поста в базе авторизированным пользователем.
        Проверка создания поста с картинкой.
        """
        post_count = Post.objects.count()
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
        form_data = {
            'text': 'Тестовый текст поста формы',
            'group': self.group.id,
            'image': uploaded,
        }
        self.authorized_client.post(
            reverse('posts:create'),
            data=form_data,
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(Post.objects.filter(
            text='Тестовый текст поста формы',
            group=self.group.id,
        ).exists())
        post = Post.objects.latest('id')
        self.assertEqual(post.image.name, 'posts/small.gif')

    def test_posts_forms_edit_post(self):
        """Редактирование поста авторизированным пользователем."""
        form_data = {
            'text': 'Новый текст поста формы',
            'group': self.group.id,
        }
        self.authorized_client.post(reverse(
            'posts:edit',
            kwargs={'post_id': self.post.id},
        ), data=form_data)
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id},
        ))
        self.assertEqual((
            response.context['post'].text), 'Новый текст поста формы')
        self.assertTrue(Post.objects.filter(
            text='Новый текст поста формы',
            group=self.group.id,
        ).exists())

    def test_posts_forms_guest_user_create_post(self):
        """Создание формы поста в базе неавторизированным пользователем."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст поста формы',
            'group': self.group.id,
        }
        self.guest_user.post(
            reverse('posts:create'),
            data=form_data,
        )
        self.assertEqual(Post.objects.count(), post_count)
        response = self.guest_user.get('/create/')
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_authorized_user_create_comment(self):
        """Создание коментария в базе авторизированным пользователем."""
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            text='Тестовый текст поста формы',
            author=self.user)
        form_data = {
            'text': 'Тестовый коментарий поста'
            }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.id}),
            data=form_data,
            follow=True)
        comment = Comment.objects.latest('id')
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post_id, post.id)
        self.assertRedirects(
            response, reverse('posts:post_detail', args={post.id}))


    def test_nonauthorized_user_create_comment(self):
        """Создание комментария в базе неавторизированным пользователем."""
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            text='Текст поста для редактирования',
            author=self.user)
        form_data = {
            'text': 'Тестовый коментарий'
            }
        response = self.guest_user.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.id}),
            data=form_data,
            follow=True)
        redirect = reverse('login') + '?next=' + reverse(
            'posts:add_comment', kwargs={'post_id': post.id})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertRedirects(response, redirect)
