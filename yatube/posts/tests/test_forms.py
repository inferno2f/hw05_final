import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.small_image = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.jpeg",
            content=cls.small_image,
            content_type="image/jpeg",
        )
        cls.user = User.objects.create_user(username="John")
        cls.group = Group.objects.create(
            title="Group title",
            description="Group description",
            slug="test-slug",
        )
        cls.post = Post.objects.create(
            text="text",
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
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

    def test_create_post_form(self):
        """
        Testing fields and expected types of fields for post creation form
        """
        response = self.authorized_client.get(reverse("posts:create_post"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
            "image": forms.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                saved_post_form = response.context["form"].fields.get(value)
                self.assertIsInstance(saved_post_form, expected)

    def test_create_post_success(self):
        """
        Testing the creation and addition of a new post to the db.
        """
        posts_count = Post.objects.count()
        new_img = SimpleUploadedFile(
            name="small.jpeg",
            content=self.small_image,
            content_type="image/jpeg",
        )
        form_data = {
            "text": "This is a new text",
            "author": self.user,
            "group": self.group.id,
            "image": new_img,
        }
        response = self.authorized_client.post(
            reverse("posts:create_post"), form_data, follow=True
        )
        created_post = Post.objects.latest("id")
        self.assertRedirects(
            response,
            reverse(
                "posts:profile",
                kwargs={"username": created_post.author.username},
            ),
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(created_post.text, form_data["text"])
        self.assertEqual(created_post.author, form_data["author"])
        self.assertEqual(created_post.group.id, form_data["group"])
        self.assertTrue(created_post.image)

    def test_edit_post_non_author(self):
        """
        Testing that post can not be edited by non-author users.
        """
        non_author_user = User.objects.create_user(username="Bob")
        authorized_non_author = Client()
        authorized_non_author.force_login(non_author_user)
        response = authorized_non_author.get(
            reverse("posts:update_post", kwargs={"post_id": self.post.id})
        )
        posts_count = Post.objects.count()
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_edit_success(self):
        """
        Testing edit post functionality.
        Ensuring that the existing record is being updated.
        No new records should be added to the db.
        """
        posts_count = Post.objects.count()
        form_data = {"text": "This is an edited text"}
        response = self.authorized_client.post(
            reverse("posts:update_post", kwargs={"post_id": self.post.id}),
            form_data,
            follow=True,
        )
        edited_post = Post.objects.latest("id")
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(edited_post.text, form_data["text"])

    def test_add_comment(self):
        """
        Authorized user should be able to post commet from post_detail page
        """
        post_comment_count = self.post.comments.count()
        form = {"text": "test comment"}
        response = self.authorized_client.post(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id}),
            form,
            follow=True,
        )
        new_comment = Comment.objects.latest("id")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(new_comment.text, form["text"])
        self.assertEqual(new_comment.author, self.user)
        self.assertEqual(self.post.comments.count(), post_comment_count + 1)

    def test_unauthorized_user_add_comment(self):
        """
        Unauthorized users shouldn't be able to leave comments
        """
        response = self.client.get(
            reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response,
            reverse("users:login")
            + "?next="
            + reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
        )
