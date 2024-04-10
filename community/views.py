from django.shortcuts import render, redirect, get_object_or_404
from .models import Post, Comment, Reply
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone


def post_list(request):
    query = request.GET.get('q', '')
    page_number = request.GET.get('page')
    today = timezone.now().date()

    posts = Post.objects.filter(title__icontains=query).order_by('-date')

    paginator = Paginator(posts, 16)
    page_obj = paginator.get_page(page_number)

    return render(request, 'community/post_list.html', {'page_obj': page_obj, 'today': today, 'query': query})

def post_create(request):
    if request.method == 'POST':
        post = Post()
        post.title = request.POST["title"]
        post.content = request.POST["content"]
        post.author = request.user
        if "image" in request.FILES:
            post.image = request.FILES["image"]
        post.save()
        return redirect('community:post_list')
    return render(request, 'community/post_create.html')

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.hit += 1
    post.save()
    comments = Comment.objects.filter(post__pk=pk).order_by('-date')
    if request.method == 'POST':
        if request.user.is_authenticated:
            if post.like_users.filter(pk=request.user.pk).exists():
                post.like_users.remove(request.user)
                post.like -= 1
            else:
                post.like_users.add(request.user)
                post.like += 1
            post.save()
            return JsonResponse({'like_count': post.like})
        else:
            messages.warning(request, "로그인 후 다시 시도해 주세요.")
    return render(request, 'community/post_detail.html', {'post': post, 'comments': comments})

def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        post.title = request.POST["title"]
        post.content = request.POST["content"]
        post.author = request.user
        if "image" in request.FILES:
            post.image = request.FILES["image"]
        post.save()
        return redirect('community:post_detail', pk=post.pk)
    return render(request, 'community/post_edit.html', {'post': post})

def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        post.delete()
        return redirect('community:post_list')
    return render(request, 'community/post_detail.html', {'post': post})