from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

app_name = "posts"

urlpatterns = [
    path("", views.index, name="index"),
    path("group/<slug:slug>/", views.group_posts, name="group_list"),
    path("profile/<str:username>/", views.profile, name="profile"),
    path("posts/<int:post_id>/", views.post_detail, name="post_detail"),
    path(
        "posts/<int:post_id>/comment/",
        login_required(views.add_comment),
        name="add_comment",
    ),
    path("create/", login_required(views.create_post), name="create_post"),
    path(
        "posts/<int:post_id>/edit/",
        login_required(views.edit_post),
        name="update_post",
    ),
    path(
        "profile/<str:username>/follow/",
        views.follow,
        name="profile_follow",
    ),
    path(
        "profile/<str:username>/unfollow/",
        views.unfollow,
        name="profile_unfollow",
    ),
    path("follow/", views.follow_index, name="follow_index"),
]
