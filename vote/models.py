from django.db import models
# Create your models here.


class School(models.Model):
    school_name = models.CharField(max_length=100)
    school_image = models.ImageField(upload_to='school_image', null=True)
    school_address = models.CharField(max_length=100, null=True)
    school_score = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    susi_school_pdf = models.FileField(upload_to="susi_school_pdf", null=True)
    jungsi_school_pdf = models.FileField(upload_to="jungsi_school_pdf", null=True)

    def __str__(self):
        return self.school_name