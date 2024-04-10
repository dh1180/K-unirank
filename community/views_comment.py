from django.shortcuts import redirect, get_object_or_404
from .models import Post, Comment, Reply
from django.contrib import messages


def comment_create(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.user.is_authenticated and request.method == 'POST':
        comment = Comment()
        comment.post = post
        comment.author = request.user
        comment.content = request.POST["content"]
        comment.save()
        return redirect('community:post_detail', pk=post.pk)
    messages.warning(request, "로그인 후 다시 시도해 주세요.")
    return redirect('community:post_detail', pk=post.pk)


def comment_delete(request, post_pk, comment_pk):
    if request.user.is_authenticated:
        comment = get_object_or_404(Comment, pk=comment_pk)
        if request.user == comment.author:
            comment.delete()
    return redirect('community:post_detail', pk=post_pk)


def reply_create(request, post_pk, comment_pk):
    comment = get_object_or_404(Comment, pk=comment_pk)
    if request.user.is_authenticated and request.method == 'POST':
        reply = Reply()
        reply.comment = comment
        reply.author = request.user
        reply.content = request.POST["content"]
        reply.save()
        return redirect('community:post_detail', pk=post_pk)
    messages.warning(request, "로그인 후 다시 시도해 주세요.")
    return redirect('community:post_detail', pk=post_pk)


def reply_delete(request, post_pk, reply_pk):
    if request.user.is_authenticated:
        reply = get_object_or_404(Reply, pk=reply_pk)
        if request.user == reply.author:
            reply.delete()
    return redirect('community:post_detail', pk=post_pk)