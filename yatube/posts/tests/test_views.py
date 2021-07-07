import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post, User

TEMP_MEDIA = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class Test(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='kekoslav')
        image = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='image.gif',
            content=image,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Test Group',
            slug='testing-slug',
            description='Test Group'
        )
        cls.post = Post.objects.create(
            text='Test test',
            image=uploaded,
            author=cls.user,
            group=cls.group
        )
        cls.temp_page_named = {
            'posts/index.html': reverse('index'),
            'posts/new_post.html': reverse('new_post'),
            'posts/group.html': (
                reverse('group_posts', kwargs={'slug': 'testing-slug'})
            ),
        }

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def post_context_test(self, post):
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.image, self.post.image)

    def test_pages_use_current_template(self):
        """Тест использования корректрого шаблона при обращение через name.."""
        for template, reverse_name in self.temp_page_named.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_context_in_template(self):
        """Тест контекста index............................................."""
        response = self.authorized_client.get(reverse('index'))
        post1 = response.context['page'][0]
        self.post_context_test(post1)

    def test_new_post_visible_in__group(self):
        """Тест видимости нового поста в группе............................."""
        response = self.authorized_client.get(reverse(
            'group_posts', kwargs={'slug': self.group.slug})
        )
        post = response.context['page'][0]
        group = post.group
        self.assertEqual(group, self.group)

    def test_new_post_not_in_another_group(self):
        """Тест появления поста в прочих группах............................"""
        post = Post.objects.create(
            text='Test test',
            author=self.user,
        )
        response = self.authorized_client.get(reverse(
            'group_posts', kwargs={'slug': self.group.slug})
        ).context.get('page')
        self.assertNotIn(post, response)

    def test_group_context_in_template(self):
        """Тест контекста group............................................."""
        response = self.authorized_client.get(reverse(
            'group_posts', kwargs={'slug': self.group.slug})
        )
        post = response.context['page'][0]
        self.assertEqual(self.group.title, post.group.title)
        self.assertEqual(self.group.slug, post.group.slug)
        self.assertEqual(self.group.description, post.group.description)
        self.post_context_test(post)

    def test_new_post_post_edit_context_in_template(self):
        """Тест контекста new_post, edit_post..............................."""
        url = [
            reverse('new_post'),
            reverse('edit', kwargs={
                'username': self.user.username, 'post_id': self.post.id})
        ]
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField
        }
        for adress in url:
            response = self.authorized_client.get(adress)
            for value, field in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(form_field, field)

    def test_profile_context_in_template(self):
        """Тест контекста profile..........................................."""
        url = reverse('profile', kwargs={'username': self.user.username})
        response = self.authorized_client.get(url)
        context = response.context['author']
        self.assertEqual(context, self.post.author)
        test_page = response.context['page'][0]
        self.post_context_test(test_page)

    def test_post_context_in_template(self):
        """Тест контекста post.............................................."""
        url = reverse('post', kwargs={
            'username': self.user.username, 'post_id': self.post.id
        })
        response = self.authorized_client.get(url)
        post1 = response.context['post']
        self.post_context_test(post1)

    def test_cache(self):
        """Тест кэша........................................................"""
        # Первый вызов для проверки
        self.authorized_client.get(reverse('index'))
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(response.context, None)
        post = Post.objects.create(
            author=self.user,
            text='CACHE')
        # Вызов для проверки после создания поста
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(response.context, None)
        cache.clear()
        # Вызов для проверки после очистки кэша
        response = self.authorized_client.get(reverse('index'))
        self.assertNotEqual(response.context, None)
        self.assertEqual(response.context['page'][0], post)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='kekoslav')
        cls.client = Client(cls.user)
        cls.group = Group.objects.create(
            title='Test Group',
            slug='testing-slug',
            description='Test Group'
        )
        for i in range(13):
            cls.post = Post.objects.create(
                text='Test ' * i,
                author=cls.user,
                group=cls.group
            )

        cls.sub_test_url = [
            reverse('index'),
            reverse('group_posts', kwargs={'slug': cls.group.slug}),
            reverse('profile', kwargs={'username': cls.user.username})
        ]

    def setUp(self):
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """Тест 1-ой страницы паджинатора на то что приходит 10 постов......"""
        for adress in self.sub_test_url:
            with self.subTest(adress=adress):
                response = self.client.get(adress).context.get('page')
                self.assertEqual(
                    response.paginator.page(1).object_list.count(), 10)

    def test_second_page_contains_three_records(self):
        """Тест 2-ой страницы паджинатора на то что приходит 3 поста........"""
        cache.clear()
        for adress in self.sub_test_url:
            with self.subTest(adress=adress):
                response = self.client.get(adress).context.get('page')
                self.assertEqual(
                    response.paginator.page(2).object_list.count(), 3)


class CommentAndFollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='kekoslav')
        cls.user2 = User.objects.create_user(username='kekw')

        cls.post = Post.objects.create(
            text='example',
            author=cls.user1
        )

    def setUp(self):
        self.client_guest = Client()
        self.client_auth = Client()

        self.client_auth.force_login(self.user1)

    def test_auth_user_can_follow(self):
        """Тест авторизованный пользователь может подписаться..............."""
        self.client_auth.post(
            reverse('profile_follow', kwargs={'username': self.user2}),
            follow=True
        )
        is_follow = Follow.objects.filter(
            user=self.user1, author=self.user2
        ).count()
        self.assertEqual(is_follow, 1)

    def test_auth_user_can_unfollow(self):
        """Тест того что пользователь может отписаться......................"""
        Follow.objects.create(user=self.user1, author=self.user2)
        self.client_auth.post(
            reverse('profile_unfollow', kwargs={'username': self.user2}),
            follow=True
        )

        is_unfollow = Follow.objects.filter(
            user=self.user1, author=self.user2
        ).count()
        self.assertEqual(is_unfollow, 0)

    def test_auth_user_can_comment_post(self):
        """Тест того что пользователь может оставить коммент................"""
        url_kwargs = {'username': self.user1, 'post_id': self.post.id}
        form = {'text': 'TEST_TEXT'}
        response_status_test = self.client_auth.post(
            reverse('add_comment', kwargs=url_kwargs),
            data=form,
            follow=True
        )
        comments_count = Comment.objects.filter(
            author=self.user1,
            post=self.post.id
        ).count()
        self.assertEqual(response_status_test.status_code, HTTPStatus.OK)
        self.assertTrue(Comment.objects.filter(
            text=form['text'],
            post=self.post,
            author=self.user1
        ).exists())
        self.assertEqual(comments_count, 1)

    def test_guest_user_cant_comment_post(self):
        """Тест что неавторизованный пользователь редиректит на логин......."""
        url_kwarg = {'username': self.user1, 'post_id': self.post.id}
        response = self.client_guest.post(
            reverse('add_comment', kwargs=url_kwarg),
            data={'text': 'TEST_TEXT'},
            follow=True
        )
        login_url = reverse('login')
        new_comment_url = reverse('add_comment', kwargs=url_kwarg)
        login_redirects = f'{login_url}?next={new_comment_url}'
        self.assertRedirects(
            response, login_redirects, target_status_code=HTTPStatus.OK
        )

        comments_count = Comment.objects.filter(
            author=self.user1, post=self.post.id).count()
        self.assertEqual(comments_count, 0)

    def test_new_post_appears_in_follow_index(self):
        """Тест того что пост появился в списке у подписки.................."""
        post = Post.objects.create(
            text='example2',
            author=self.user2
        )
        Follow.objects.create(
            user=self.user1, author=self.user2
        )
        response = self.client_auth.get(reverse('follow_index'))
        self.assertIn(post, response.context['page'])

    def test_not_follow_post_dont_appears_in_follow_index(self):
        """Тест того что пост не появился не у подписчика..................."""
        Post.objects.create(
            text='example',
            author=self.user2
        )
        follow_page = self.client_auth.get(
            reverse('follow_index')
        ).context.get('page')
        self.assertEqual(follow_page.paginator.object_list.count(), 0)
