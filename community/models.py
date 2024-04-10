from django.db import models
from django.contrib.auth.models import User


class Post(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    hit = models.IntegerField(default=0)
    like = models.IntegerField(default=0)
    like_users = models.ManyToManyField(User, related_name='like_posts')
    date = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='community_thumbnail', null=True)
    content = models.TextField()

    def get_comment_count(self):
        return Comment.objects.filter(post=self).count() + Reply.objects.filter(comment__post=self).count()

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def get_reply(self):
        return Reply.objects.filter(comment=self)

    def __str__(self):
        return self.content


class Reply(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content