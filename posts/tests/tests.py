from django.core.cache import cache
from django.urls import reverse
from django.test import Client, TestCase
from posts.models import User


class CacheTest(TestCase):
    def setUp(self):
        self.first_client = Client()
        self.second_client = Client()
        self.user = User.objects.create_user(username='user1', )
        self.first_client.force_login(self.user)

    def test_cache(self):
        cache.clear()
        self.second_client.get(reverse('posts:index'))
        self.first_client.post(reverse('posts:new_post'), {'text': 'New post'})
        response = self.second_client.get(reverse('posts:index'))
        self.assertNotContains(response, 'New post')
