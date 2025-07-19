from django.db import models

class School(models.Model):
    school_name = models.CharField(max_length=100)
    school_image = models.ImageField(upload_to='school_image', null=True, blank=True)
    school_address = models.CharField(max_length=100, null=True, blank=True)

    # Glicko-2 레이팅 시스템
    rating = models.FloatField(default=1500)        # 기본 레이팅
    rd = models.FloatField(default=350)             # 레이팅 편차 (불확실성)
    volatility = models.FloatField(default=0.06)    # 변동성 (변화율)

    # 경기 기록
    win_tournament_count = models.BigIntegerField(default=0)
    win_match_count = models.BigIntegerField(default=0)
    match_count = models.BigIntegerField(default=0)

    def __str__(self):
        return self.school_name


class PreviousRank(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    date = models.DateField()
    rank = models.IntegerField()

    def __str__(self):
        return f"{self.date} - {self.school.school_name}: {self.rank}위"
