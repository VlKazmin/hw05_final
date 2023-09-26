from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import paginate

PAGINATE_BY: int = 10


def index(request):
    posts = Post.objects.select_related("author", "group").all()
    template = "posts/index.html"
    context = {"page_obj": paginate(request, posts, PAGINATE_BY)}
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    # posts = Post.objects.filter(group=group)
    posts = Post.objects.select_related("author", "group").filter(group=group)
    template = "posts/group_list.html"
    context = {
        "group": group,
        "posts": posts,
        "page_obj": paginate(request, posts, PAGINATE_BY),
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    user_posts = Post.objects.select_related("author", "group").filter(
        author=author
    )
    following = (
        request.user.is_authenticated
        and request.user.follower.filter(author=author).exists()
    )
    template = "posts/profile.html"
    context = {
        "author": author,
        "page_obj": paginate(request, user_posts, PAGINATE_BY),
        "following": following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    posts_count = Post.objects.filter(
        author__username=post.author.username
    ).count()
    form = CommentForm()
    comments = post.comments.select_related("author").all()
    template = "posts/post_detail.html"
    context = {
        "post": post,
        "posts_count": posts_count,
        "form": form,
        "comments": comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("posts:profile", post.author)

    template = "posts/create_post.html"
    context = {
        "form": form,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )

    if request.user != post.author:
        return redirect("posts:post_detail", post_id)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("posts:post_detail", post_id)

    template = "posts/create_post.html"
    context = {
        "form": form,
        "is_edit": True,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    user_posts = Post.objects.filter(author__following__user=request.user)
    template = "posts/follow.html"
    context = {
        "page_obj": paginate(request, user_posts, PAGINATE_BY),
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect("posts:profile", username=username)


@login_required
def delete_message(request, post_id):
    message = get_object_or_404(Post, pk=post_id, author=request.user)
    template = "delete_message.html"

    if request.method == "POST":
        message.delete()
        return redirect("posts:index")

    return render(request, template)
