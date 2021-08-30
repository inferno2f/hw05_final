from django.test import TestCase
from http import HTTPStatus
from django.urls import reverse


class AboutURLTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.url_template_list = {
            reverse("about:author"): "about/author.html",
            reverse("about:tech"): "about/tech.html",
        }

    def test_about_urls_respond(self):
        for url in self.url_template_list:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_template_usage(self):
        for url, template in self.url_template_list.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertTemplateUsed(response, template)
