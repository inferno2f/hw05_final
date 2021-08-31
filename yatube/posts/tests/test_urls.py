from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username="John")
        cls.group = Group.objects.create(
            title="Group title",
            description="Group description",
            slug="test-slug",
        )
        cls.post = Post.objects.create(
            text="text", author=cls.user, group=cls.group
        )
        cls.url_template_list = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", kwargs={"slug": cls.group.slug}
            ): "posts/group_list.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": cls.post.id}
            ): "posts/post_detail.html",
            reverse(
                "posts:profile", kwargs={"username": cls.user.username}
            ): "posts/profile.html",
            reverse("posts:create_post"): "posts/create_post.html",
            reverse(
                "posts:update_post", kwargs={"post_id": cls.post.id}
            ): "posts/create_post.html",
            reverse("posts:follow_index"): "posts/follow.html",
        }

    def setUp(self) -> None:
        self.guest_client = Client()
        self.user = User.objects.get(username="John")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_all_pages_respond(self):
        for address in self.url_template_list.keys():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_correct_templates_used_for_pages(self):
        for address, template in self.url_template_list.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_guest_client_is_redirected(self):
        edit_url = reverse(
            "posts:update_post", kwargs={"post_id": self.post.id}
        )
        create_url = reverse("posts:create_post")
        edit_request = self.guest_client.get(edit_url, follow=True)
        create = self.guest_client.get(create_url, follow=True)
        self.assertRedirects(
            create, reverse("users:login") + "?next=" + create_url
        )
        self.assertRedirects(
            edit_request, reverse("users:login") + "?next=" + edit_url
        )

    def test_non_existant_page(self):
        response = self.guest_client.get("/some_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_page_404(self):
        """
        Assert custom template is used when address not found
        """
        response = self.client.get("/some_page/")
        self.assertTemplateUsed(response, "core/404.html")
