from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum, Avg
# Create your models here.


class School(models.Model):
    school_name = models.CharField(max_length=100)
    school_image = models.ImageField(upload_to='school_image', null=True)
    school_address = models.CharField(max_length=100, null=True)
    voted_users = models.ManyToManyField(User, related_name='voted_school')
    susi_school_pdf = models.FileField(upload_to="susi_school_pdf", null=True)
    jungsi_school_pdf = models.FileField(upload_to="jungsi_school_pdf", null=True)
    
    def get_average_score(self):
        average_score = School_score.objects.filter(school=self).aggregate(Avg('individual_score'))
        return average_score['individual_score__avg']

    def __str__(self):
        return self.school_name


class School_score(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    voted_user = models.ForeignKey(User, on_delete=models.CASCADE)
    individual_score = models.IntegerField(default=0)