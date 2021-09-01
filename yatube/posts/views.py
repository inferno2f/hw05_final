from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User

LIM = settings.PAGINATION_LIMIT


@cache_page(20)
@vary_on_cookie
def index(request):
    posts = Post.objects.select_related("group", "author").all()
    paginator = Paginator(posts, LIM)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
    }
    template = "posts/index.html"
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    paginator = Paginator(group.posts.select_related("author").all(), LIM)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "group": group,
        "page_obj": page_obj,
    }
    template = "posts/group_list.html"
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    is_following = False
    if not request.user.is_anonymous and request.user != author:
        is_following = Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    paginator = Paginator(author.posts.select_related("group").all(), LIM)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "author": author,
        "page_obj": page_obj,
        "following": is_following,
    }
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related(
            "author",
            "group",
        ),
        id=post_id,
    )
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    comments = post.comments.filter(post=post_id).select_related("author")
    context = {"post": post, "form": form, "comments": comments}
    return render(request, "posts/post_detail.html", context)


@login_required
def create_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("posts:profile", request.user.username)
    return render(request, "posts/create_post.html", {"form": form})


@login_required
def edit_post(request, post_id):
    cur_post = get_object_or_404(Post, id=post_id)

    if cur_post.author != request.user:
        return redirect("posts:post_detail", cur_post.id)

    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=cur_post
    )
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id)
    return render(
        request,
        "posts/create_post.html",
        {"form": form, "is_edit": True, "post_id": cur_post.id},
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id)


@login_required
def follow(request, username):
    """
    Add new author to user's subscription list
    """
    author = get_object_or_404(User, username=username)
    user = request.user
    if user != author:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect("posts:profile", username)


@login_required
def unfollow(request, username):
    """
    Remove author from user's subscription list
    """
    author = get_object_or_404(User, username=username)
    user = request.user
    subscription = Follow.objects.filter(user=user, author=author)
    subscription.delete()
    return redirect("posts:profile", username)


@login_required
def follow_index(request):
    """
    Will dislpay posts only from user's subscriptions
    """
    posts = (
        Post.objects.filter(author__following__user=request.user)
        .select_related(
            "author",
            "group",
        )
    )
    paginator = Paginator(posts, LIM)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
    }
    return render(request, "posts/follow.html", context)
