from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Group, Post, Follow

User = get_user_model()


def page_paginator(request, post_list):
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return page


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    return render(request,
                  'index.html',
                  {'page': page_paginator(request, post_list)}
                  )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    return render(request,
                  'group.html',
                  {'group': group,
                   'page': page_paginator(request, post_list)}
                  )


@login_required
def new_post(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:index')
    return render(request, 'new.html', {'form': form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    edit = author == request.user
    post_list = author.posts.all()
    post_count = post_list.count()
    # post_count = author.posts.count()
    context = {'post_count': post_count,
               'author': author,
               'page': page_paginator(request, post_list),
               'edit': edit}
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    author = post.author
    edit = author == request.user
    post_count = author.posts.count()
    form = CommentForm(request.POST or None)

    context = {'post_count': post_count,
               'post': post,
               'author': author,
               'edit': edit,
               'form': form}
    return render(request, 'post.html', context)


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if request.user != post.author:
        return redirect('posts:post',
                        post_id=post.id,
                        username=post.author.username)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)

    if form.is_valid():
        form.save()
        return redirect('posts:post',
                        username=request.user.username,
                        post_id=post_id)

    return render(request, 'new.html', {'form': form, 'edit': True,
                                        'post': post})


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)

    if form.is_valid():
        form.instance.author = request.user
        form.instance.post = post
        form.save()
    return redirect('posts:post',
                    username=username,
                    post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html',
                  {'page': page, 'paginator': paginator})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect('posts:profile', username)
    Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=user, author=author).delete()
    return redirect('posts:profile', username)


def profile(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = Follow.objects.filter(user__username=user,
                                      author=author).exists()
    return render(
        request, 'profile.html',
        {'author': author, 'page': page,
         'paginator': paginator, 'following': following}
    )
