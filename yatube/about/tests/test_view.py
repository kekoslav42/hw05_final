from django.test import Client, TestCase
from django.urls import reverse


class StaticURLTests(TestCase):
    def setUp(self):
        self.template_name = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech')
        }
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Тест URL, генерируемый при помощи имени.........................."""
        for adress in self.template_name.values():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, 200)

    def test_about_url_uses_correct_template(self):
        """Тест что при запросе применяется правильный темплейт............."""
        for template, adress in self.template_name.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)
