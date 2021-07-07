from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


@cache_page(15, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'posts/index.html',
        {'page': page, }
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.posts.all()
    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'posts/group.html',
        {'group': group, 'page': page}
    )


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts_list = author.posts.all()
    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    user = request.user
    following = Follow.objects.filter(
        user__username=user, author=author
    ).exists() if user.is_authenticated else False

    return render(
        request,
        'posts/profile.html',
        {'author': author, 'page': page, 'following': following}
    )


def post_view(request, username, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author'),
        id=post_id, author__username=username
    )
    form = CommentForm()
    comments = post.comments.all()
    # Заметил очень поздно баг,
    # и там получается на странице поста предлагало подписаться
    # в общем косяк ибо в шаблон поста то не передавалось Following
    following = Follow.objects.filter(
        user__username=request.user,
        author=post.author
    ).exists() if request.user.is_authenticated else False
    return render(
        request,
        'posts/post.html',
        {'post': post,
         'form': form,
         'comments': comments,
         'following': following}
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(
            request,
            'posts/new_post.html',
            {'form': form, 'is_create': True}
        )

    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('index')


# Это я для себя уже больше, можешь даже не смотреть =)
# Это же уже не входит в обучение
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user == post.author:
        post.delete()
    return redirect('index')
    # баг пофиксить до 11.07
    # Дабл клик выходит в 404
    # Комменты так же...
    # Использую я то or 404 значит ли что это баг.


@login_required
def edit_post(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if request.user.username == username:
        if not form.is_valid():
            return render(
                request,
                'posts/new_post.html',
                {'form': form,
                 'post': post}
            )
        form.save()
    return redirect('post', username=username, post_id=post_id)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if not form.is_valid():
        return render(
            request,
            'posts/post.html',
            {'form': form,
             'post': post}
        )
    comment = form.save(commit=False)
    comment.author = request.user
    comment.post = post
    comment.save()
    return redirect('post', username=username, post_id=post_id)


# Тоже для себя
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    # Проверка что пользователь автор коммента или автор поста
    if request.user == comment.author or request.user == comment.post.author:
        comment.delete()
    return redirect(
        'post',
        username=comment.post.author,
        post_id=comment.post.pk
    )


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'posts/follow.html',
        {'page': page, 'paginator': paginator}
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    # Никогда бы не подумал что так можно
    Follow.objects.filter(
        user=request.user,
        author__username=username
    ).delete()
    return redirect('profile', username=username)


def page_not_found(request, exception=None):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)
