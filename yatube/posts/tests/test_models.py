from ..models import Group, Post
from django.contrib.auth import get_user_model
from django.test import TestCase


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username="author")
        cls.post = Post.objects.create(
            text="This is a test text longer than 15 chars.",
            author=cls.user,
        )

    def test_post_model_has_a_descriptive_str(self):
        post_expected = self.post.text[:15]
        self.assertEqual(post_expected, str(self.post))

    def test_post_model_has_verbose_name(self):
        verbose_name_post = self.post._meta.get_field("text").verbose_name
        self.assertIsNotNone(
            verbose_name_post, "Задайте verbose_name для поста"
        )

    def test_post_model_has_help_text(self):
        help_text_post = self.post._meta.get_field("text").help_text
        self.assertIsNotNone(help_text_post, "Задайте help_text для поста")


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Title", slug="SlugField", description="Description"
        )

    def test_group_model_has_a_descriptive_str(self):
        group_expected = self.group.title
        self.assertEqual(group_expected, str(self.group))

    def test_group_model_has_verbose_name(self):
        verbose_name_group = self.group._meta.get_field("title").verbose_name
        self.assertIsNotNone(
            verbose_name_group, "Задайте verbose_name для группы"
        )

    def test_group_model_has_help_text(self):
        help_text_group = self.group._meta.get_field("title").help_text
        self.assertIsNotNone(
            help_text_group, "Задайте help_text для поля группы"
        )
