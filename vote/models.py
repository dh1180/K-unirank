from django.db import models
# Create your models here.


class School(models.Model):
    school_name = models.CharField(max_length=100)
    school_image = models.ImageField(upload_to='school_image', null=True)
    school_address = models.CharField(max_length=100, null=True)
    school_score = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    win_tournament_count = models.BigIntegerField(default=0)
    win_match_count = models.BigIntegerField(default=0)
    match_count = models.BigIntegerField(default=0)

    def __str__(self):
        return self.school_name
    
    
class PreviousRank(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    rank = models.IntegerField()

    class Meta:
        unique_together = ('school', 'date')  # 하루에 한 번만 기록