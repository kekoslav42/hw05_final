from django.test import TestCase

from ..models import Group, Post, User


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

    def test_title(self):
        """Тест метода str у Group возращающего str........................."""
        title = Test.group.title
        self.assertEqual(title, str(self.group))

    def test_text(self):
        """Тест метода str у Post возращающего str[:15]....................."""
        text = Test.post.text[:15]
        self.assertEqual(text, str(self.post))
