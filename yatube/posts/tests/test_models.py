from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Тестовый пользователь')
        cls.group = Group.objects.create(title='Тестовая группа')
        cls.post = Post.objects.create(
            text='Тестовый пост длинной более 15 символов',
            author=cls.user,
            group=cls.group
        )

    def test_post_verbose_name(self):
        """verbose_name в полях Post совпадает с ожидаемым"""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_group_verbose_name(self):
        """verbose_name в полях Group совпадает с ожидаемым"""
        group = PostModelTest.group
        field_verboses = {
            'title': 'Наименование группы',
            'description': 'Описание группы',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).verbose_name, expected)

    def test_post_help_text(self):
        """help_texts в полях Post совпадает с ожидаемым"""
        post = PostModelTest.post
        help_texts = {
            'text': 'Здесь напишите текст публикации',
            'pub_date': 'Укажите дату публикации',
            'author': 'Укажите автора публикации',
            'group': 'Укажите группу для публикации',
        }
        for value, expected in help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_group_help_text(self):
        """help_texts в полях Group совпадает с ожидаемым"""
        group = PostModelTest.group
        help_texts = {
            'title': 'Укажите наименование группы',
            'description': 'Уточните описание группы',
        }
        for value, expected in help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).help_text, expected)

    def test_post_text_str(self):
        """выводим только первые пятнадцать символов поста"""
        post = PostModelTest.post
        text = post.text
        self.assertEqual(str(post), text[:15])

    def test_group_title_str(self):
        """название группы совпадает"""
        group = PostModelTest.group
        title = str(group)
        self.assertEqual(title, group.title)
