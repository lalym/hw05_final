import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

from posts.models import Group, Post, Follow

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(title='Тестовое название',
                                         slug='test-slug',
                                         description='Тестовое описание')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост длинной более 15 символов',
            author=cls.user,
            group=cls.group,
            image=uploaded
        )
        cls.templates_pages_names = {
            'index.html': reverse('posts:index'),
            'group.html': reverse('posts:group_posts',
                                  kwargs={'slug': 'test-slug'}),
            'new.html': reverse('posts:new_post')
        }

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_context_in_template_index(self):
        """
        Шаблон index сформирован с правильным контекстом.
        При создании поста с указанием группы,
        этот пост появляется на главной странице сайта.
        """
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        last_post = response.context['page'][0]
        self.assertEqual(last_post, self.post)

    def test_context_in_template_group(self):
        """
        Шаблон group сформирован с правильным контекстом.
        При создании поста с указанием группы,
        этот пост появляется на странице этой группы.
        """
        response = self.authorized_client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}))
        test_group = response.context['group']
        test_post = response.context['page'][0].__str__()
        self.assertEqual(test_group, self.group)
        self.assertEqual(test_post, self.post.__str__())

    def test_context_in_template_new_post(self):
        """Шаблон new сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:new_post'))

        form_fields = {'group': forms.fields.ChoiceField,
                       'text': forms.fields.CharField,
                       'image': forms.fields.ImageField,
                       }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_context_in_post_edit_template(self):
        """Шаблон редактирования поста сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'username': self.user.username,
                            'post_id': self.post.id}),
        )

        form_fields = {
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_context_in_template_profile(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user.username})
        )

        profile = {'author': self.post.author}

        for value, expected in profile.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, expected)

        test_page = response.context['page'][0]
        self.assertEqual(test_page, self.user.posts.all()[0])

    def test_context_in_template_post(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post',
                    kwargs={'username': self.user.username,
                            'post_id': self.post.id})
        )

        profile = {'post_count': self.user.posts.count(),
                   'author': self.post.author,
                   'post': self.post}

        for value, expected in profile.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, expected)

    def test_post_not_add_another_group(self):
        """
        При создании поста с указанием группы,
        этот пост НЕ попал в группу, для которой не был предназначен.
        """
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page'][0]
        group = post.group
        self.assertEqual(group, self.group)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test User')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        for count in range(13):
            cls.post = Post.objects.create(
                text=f'Тестовый пост номер {count}',
                author=cls.user)

    def test_first_page_contains_ten_records(self):
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_contains_three_records(self):
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(len(response.context.get('page').object_list), 3)


class TestFollow(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(title='TestGroup',
                                         slug='test_slug',
                                         description='test description')
        cls.follow_user = User.objects.create_user(username='Test Author')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.follow_user)

    def test_follow(self):
        """
        Авторизованный пользователь может
        подписываться на других пользователей
        """
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username})
        )
        follow = Follow.objects.first()
        self.assertEqual(Follow.objects.count(), 1)
        self.assertEqual(follow.author, self.user)
        self.assertEqual(follow.user, self.follow_user)

    def test_unfollow(self):
        """
        Авторизованный пользователь может
        удалять других пользователей из подписок
        """
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username})
        )
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user.username})
        )
        self.assertFalse(Follow.objects.exists())

    def test_follow_index(self):
        """
        Новая запись пользователя появляется в ленте тех,
        кто на него подписан
        """
        cache.clear()
        Post.objects.create(
            author=self.user,
            text='new post to follow',
            group=self.group
        )
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username})
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        post = response.context['post']
        self.assertEqual(post.text, 'new post to follow')
        self.assertEqual(post.author, self.user)

    def test_not_follow_index(self):
        """
        Новая запись пользователя не появляется в ленте тех,
        кто на него не подписан
        """
        Post.objects.create(
            author=self.user,
            text='new post to follow',
            group=self.group
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(
            response.context['paginator'].count, 0
        )


class TestComments(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='User')
        cls.commenting_user = User.objects.create_user(
            username='Commenting User'
        )
        cls.post = Post.objects.create(
            text='great comment text',
            author=cls.user
        )
        cls.comment_url = reverse('posts:add_comment', kwargs={
            'username': cls.post.author.username, 'post_id': cls.post.id})

    def setUp(self):
        self.anonymous = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.commenting_user)

    def test_comment_anonymous(self):
        """
        При попытке комментировать пост пользователь
        направляется на страницу регистрации
        """
        response = self.anonymous.get(self.comment_url)
        expected_url = '/auth/login/?next={}'.format(self.comment_url)
        self.assertRedirects(response, expected_url,
                             status_code=HTTPStatus.FOUND)

    def test_comment_authorized_only(self):
        """
        Только авторизированный пользователь может комментировать посты
        """
        response = self.authorized_client.post(self.comment_url,
                                               {'text': 'new post'},
                                               follow=True)
        self.assertContains(response, 'new post')
