from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Comment, Follow, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Anthony')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для проверки...',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        expected_post_15_name = post.text[:15]
        self.assertEqual(expected_post_15_name, str(post))

    def test_group_label(self):
        """verbose_name поля group совпадает с ожидаемым."""
        post = PostModelTest.post
        verbose = post._meta.get_field('group').verbose_name
        self.assertEqual(verbose, 'Группа')

    def test_group_help_text(self):
        """help_text поля group совпадает с ожидаемым."""
        post = PostModelTest.post
        help_text = post._meta.get_field('group').help_text
        self.assertEqual(help_text, 'Группа, к которой будет относиться пост')


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Anthony')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = GroupModelTest.group
        expected_post_name = group.title
        self.assertEqual(expected_post_name, str(group))


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Anthony')
        cls.post = Post.objects.create(
            text='Тестовый пост для проверки...',
            author=cls.user,
        )
        cls.comment = Comment.objects.create(
            text='Комментарий для поста',
            author=cls.user,
            post=cls.post,
        )

    def test_сomment_str(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(self.comment.text[:15], str(self.comment))

    def test_сomment_verbose_name(self):
        """verbose_name поля comment совпадает с ожидаемым."""
        field_verboses = {
            'post': 'Пост',
            'author': 'Автор',
            'text': 'Текст комментария',
            'created': 'Создан',
            'updated': 'Обнавлен',
            'active': 'Активен',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                verbose_name = self.comment._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username='user_1')
        cls.user_2 = User.objects.create_user(username='user_2')
        cls.follow = Follow.objects.create(
            user=cls.user_1,
            author=cls.user_2,
        )

    def test_follow_str(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(
            f'{self.follow.user} подписался на {self.follow.author}',
            str(self.follow)
        )

    def test_follow_verbose_name(self):
        """verbose_name поля follow совпадает с ожидаемым."""
        field_verboses = {
            'user': 'Пользователь',
            'author': 'Автор',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                verbose_name = self.follow._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)
