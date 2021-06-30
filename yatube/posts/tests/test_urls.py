from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post, User


class TestUrls(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='kekoslav')
        cls.no_author = User.objects.create_user(username='no_author')
        cls.group = Group.objects.create(
            title='Test Group',
            slug='testing-slug',
            description='Test Group'
        )
        cls.post = Post.objects.create(
            text='Test ',
            author=cls.author,
            group=cls.group
        )
        cls.temp_url_name = {
            'posts/index.html': '/',
            'posts/group.html': f'/group/{cls.group.slug}/',
            'posts/new_post.html': '/new/',
            'posts/profile.html': f'/{cls.author.username}/',
            'posts/post.html': f'/{cls.author.username}/{cls.post.id}/'}

    def setUp(self):
        # Неавторизованный пользователь
        self.guest_client = Client()
        # Авторизованный клиент (Автор поста)
        self.client_author = Client()
        self.client_author.force_login(self.author)
        # Авторизованный клиент
        self.client_no_author = Client()
        self.client_no_author.force_login(self.no_author)

    def test_auth_user(self):
        """Тест доступа для авторизованного пользователя...................."""
        for adress in self.temp_url_name.values():
            with self.subTest(adress=adress):
                response = self.client_no_author.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_user(self):
        """тест доступа для гостя и редиректа с new/ на страницу авторизации"""
        for adress in self.temp_url_name.values():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                if response.status_code == HTTPStatus.FOUND:
                    self.assertRedirects(
                        response, '/auth/login/?next=/new/')
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_access_edit(self):
        """Тест доступа к страницы редактирования для групп пользователя...."""
        url = f'/{self.author.username}/{self.post.id}/edit/'
        response_guest = self.guest_client.get(url)
        response_author = self.client_author.get(url)
        response_no_author = self.client_no_author.get(url)
        self.assertEqual(response_guest.status_code, HTTPStatus.FOUND)
        self.assertEqual(response_no_author.status_code, HTTPStatus.FOUND)
        self.assertEqual(response_author.status_code, HTTPStatus.OK)

    def test_redirect_edit(self):
        """Тест редиректов для не автора и гостя со страницы редактирования."""
        url = f'/{self.author.username}/{self.post.id}/edit/'
        post_url = f'/{self.author.username}/{self.post.id}/'
        response_guest = self.guest_client.get(url)
        response_no_author = self.client_no_author.get(url)
        self.assertRedirects(response_guest, f'/auth/login/?next={url}')
        self.assertRedirects(response_no_author, post_url)

    def test_used_correct_templates(self):
        """Тест корректного использования темплейтов........................"""
        cache.clear()
        for template, adress in self.temp_url_name.items():
            with self.subTest(adress=adress):
                response = self.client_no_author.get(adress)
                self.assertTemplateUsed(response, template)

    def test_correct_edit_template(self):
        """Тест корректного использования темтлейта для edit пост..........."""
        url = f'/{self.author.username}/{self.post.id}/edit/'
        response = self.client_author.get(url)
        self.assertTemplateUsed(response, 'posts/new_post.html')

    # По логике это должно находиться здесь
    def test_404_page_not_found(self):
        """Тест 404 страницы ошибки........................................."""
        response = self.guest_client.get('/404/')
        self.assertTemplateUsed(response, 'misc/404.html')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_500_server_error(self):
        """Тест 500 страницы ошибки........................................."""
        response = self.guest_client.get('/500/')
        self.assertTemplateUsed(response, 'misc/500.html')
        self.assertEqual(
            response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR
        )
