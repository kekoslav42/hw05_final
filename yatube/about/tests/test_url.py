from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        self.template_name = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/'
        }
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адреса /author/, /tech/....................."""
        for adress in self.template_name.values():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, 200)

    def test_about_url_uses_correct_template(self):
        """Проверка шаблона для адреса /author/, /tech/....................."""
        for template, adress in self.template_name.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)
