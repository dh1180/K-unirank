from community.models import Post, Comment
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone


def user_profile(request):
    return render(request, 'user/user_profile.html')


def user_posts(request):
    posts = Post.objects.filter(author=request.user).order_by('-date')
    page_number = request.GET.get('page')
    today = timezone.now().date()

    paginator = Paginator(posts, 16)
    page_obj = paginator.get_page(page_number)
    return render(request, 'user/user_posts.html', {'page_obj': page_obj, 'today': today})


def change_username(request):
    present_user = request.user
    if present_user.is_authenticated:
        if request.method == 'POST':
            present_user.username = request.POST["username"]
            present_user.save()
            return render(request, 'user/user_profile.html')
        return render(request, 'user/user_profile.html')
    else:
        return render(request, 'user/user_profile', {'error': '사용자가 로그인하지 않았습니다.'})


def user_comment_posts(request):
    comment_posts = Comment.objects.filter(author=request.user).order_by('-date')
    page_number = request.GET.get('page')
    today = timezone.now().date()

    paginator = Paginator(comment_posts, 16)
    page_obj = paginator.get_page(page_number)
    return render(request, 'user/user_comment_posts.html', {'page_obj': page_obj, 'today': today})


def user_like_posts(request):
    posts = Post.objects.filter(like_users=request.user).order_by('-date')
    page_number = request.GET.get('page')
    today = timezone.now().date()

    paginator = Paginator(posts, 16)
    page_obj = paginator.get_page(page_number)
    return render(request, 'user/user_like_posts.html', {'page_obj': page_obj, 'today': today})


def user_delete(request):
    if request.method == 'POST':
        request.user.delete()
        return redirect('community:post_list')
    return render(request, 'user/user_profile')


def other_user_posts(request, author):
    posts = Post.objects.filter(author=author).order_by('-date')
    page_number = request.GET.get('page')
    today = timezone.now().date()

    paginator = Paginator(posts, 16)
    page_obj = paginator.get_page(page_number)
    return render(request, 'user/other_user_posts.html', {'page_obj': page_obj, 'author': User.objects.get(pk=author), 'today': today})

