import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User

TEMP_MEDIA = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class Test(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='kekoslav')
        cls.group = Group.objects.create(
            title='Test Group',
            slug='testing-slug',
            description='Test Group'
        )
        cls.post = Post.objects.create(
            text='Test ' * 100,
            author=cls.user,
            group=cls.group
        )
        cls.form = PostForm()

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_create_form(self):
        """Тест на создание записи в бд....................................."""
        posts = Post.objects.count()
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

        form_data = {
            'group': self.group.id,
            'text': 'Text',
            'image': uploaded,
        }

        response = self.auth_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts + 1)
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(Post.objects.filter(
            group=form_data['group'],
            text=form_data['text'],
            image='posts/image.gif'
        ).exists())

    def test_edit_form(self):
        """Тест на изменение объекта в бд..................................."""
        test_group = Group.objects.create(
            title='Test Group',
            slug='test-slug',
            description='Test Group'
        )
        form_data = {
            'group': test_group.id,
            'text': 'ABC',
        }
        url = {'username': self.user.username, 'post_id': self.post.id}
        response = self.auth_client.post(
            reverse('edit', kwargs=url),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse('post', kwargs=url))
        self.assertTrue(Post.objects.filter(
            group=form_data['group'],
            text=form_data['text']
        ).exists())
