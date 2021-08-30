import shutil
import tempfile

from django.conf import settings
from django.contrib import auth
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.http import response
from ..models import Follow, Post, Group
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        small_image = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small.jpeg", content=small_image, content_type="image/jpeg"
        )
        cls.user = User.objects.create_user(username="John")
        cls.group = Group.objects.create(
            title="Group title",
            description="Group description",
            slug="test-slug",
        )
        cls.post = Post.objects.create(
            text="This is a test text",
            author=cls.user,
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        self.guest_client = Client()
        self.user = User.objects.get(username=self.user.username)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def check_post_fields(self, context):
        self.assertEqual(context.text, self.post.text)
        self.assertEqual(context.author, self.post.author)
        self.assertEqual(context.group, self.post.group)
        self.assertEqual(context.image, self.post.image)

    def test_correct_templates_used(self):
        """Testing that each page uses correct template."""
        page_template_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): "posts/group_list.html",
            reverse(
                "posts:profile", kwargs={"username": self.user.username}
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": self.post.id}
            ): "posts/post_detail.html",
            reverse("posts:create_post"): "posts/create_post.html",
            reverse(
                "posts:update_post", kwargs={"post_id": self.post.id}
            ): "posts/create_post.html",
        }
        for reverse_name, template in page_template_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
    
    def test_page_404(self):
        """
        Assert custom template is used when address not found
        """
        response = self.guest_client.get("/some_page/")
        self.assertTemplateUsed(response, "core/404.html")

    def test_main_page_context(self):
        """Testing information from the context on the main page."""
        response = self.guest_client.get(reverse("posts:index"))
        context = response.context["page_obj"][0]
        self.check_post_fields(context)

    def test_group_page_context(self):
        """
        Testing information from the context on the group page.
        Posts should be filtered by the group name.
        """
        response = self.guest_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group.slug})
        )
        selected_group = response.context["group"]
        self.assertEqual(selected_group.title, self.group.title)
        self.assertEqual(selected_group.description, self.group.description)
        self.assertEqual(selected_group.slug, self.group.slug)
        self.assertEqual(selected_group.posts, self.group.posts)

    def test_profile_page_context(self):
        """Testing author page, all of the author's posts should be listed"""
        response = self.authorized_client.get(
            reverse("posts:profile", kwargs={"username": self.user.username})
        )
        selected_profile = response.context["author"]
        self.assertEqual(selected_profile.username, self.user.username)
        self.assertEqual(selected_profile.posts, self.user.posts)

    def test_post_detail_page_context(self):
        """Testing post detail page with information about author"""
        response = self.guest_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        context = response.context["post"]
        self.check_post_fields(context)

    def test_paginator_works_on_respective_pages(self):
        """
        Testing if paginator works on necessary pages.
        10 posts per page.
        """
        paginator_urls = {
            reverse("posts:index"),
            reverse("posts:group_list", kwargs={"slug": self.group.slug}),
            reverse("posts:profile", kwargs={"username": self.user.username}),
        }
        objs = [
            Post(
                text="New Entry",
                author=self.user,
                group=self.group,
            )
            for _ in range(12)
        ]
        Post.objects.bulk_create(objs)
        for url in paginator_urls:
            with self.subTest(url=url):
                first_page = self.authorized_client.get(url)
                second_page = self.authorized_client.get(url + "?page=2")
                self.assertEqual(len(first_page.context["page_obj"]), 10)
                self.assertEqual(len(second_page.context["page_obj"]), 3)

    def test_main_page_is_cached(self):
        """
        Asserting that main page is cached
        """
        cache.clear()
        self.client.get(reverse("posts:index"))
        Post.objects.all().delete()
        response = self.client.get(reverse("posts:index"))
        decoded = response.content.decode(encoding="UTF-8", errors="strict")
        self.assertInHTML(self.post.text, decoded)

    def test_followed_authors_page(self):
        """
        Follow feed should display posts from author followed by user.
        """
        follower = User.objects.create_user(username="Bobik")
        non_follower = User.objects.create_user(username="Lelik")
        auth_follower = Client()
        auth_non_follower = Client()
        auth_follower.force_login(follower)
        auth_non_follower.force_login(non_follower)
        Follow.objects.create(user=follower, author=self.user)
        response_sub = auth_follower.get(reverse("posts:follow_index"))
        response_non_sub = auth_non_follower.get(reverse("posts:follow_index"))
        sub_post = response_sub.context["page_obj"][0]
        self.assertEqual(sub_post.text, self.post.text)
        self.assertEqual(len(response_non_sub.context["page_obj"]), 0)
