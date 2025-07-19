from django.db import models
from vote.models import School

class Tournament(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    total_rounds = models.IntegerField()  # 4, 8, 16, 32, 64, 128, 256
    current_round = models.IntegerField(default=1)
    winner = models.ForeignKey('vote.School', on_delete=models.CASCADE, null=True, blank=True, related_name='won_tournament')
    
    def __str__(self):
        return self.name

    @property
    def progress_percentage(self):
        return (self.current_round / self.total_rounds) * 100

    def get_final_winner(self):
        if not self.is_completed:
            return None
        final_match = TournamentMatch.objects.filter(
            tournament=self,
            round_number=self.total_rounds
        ).first()
        return final_match.winner if final_match else None

class TournamentMatch(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    round_number = models.IntegerField()
    match_number = models.IntegerField()
    school1 = models.ForeignKey('vote.School', on_delete=models.CASCADE, related_name='matches_as_school1')
    school2 = models.ForeignKey('vote.School', on_delete=models.CASCADE, related_name='matches_as_school2')
    winner = models.ForeignKey('vote.School', on_delete=models.CASCADE, null=True, blank=True, related_name='won_matches')
    loser = models.ForeignKey('vote.School', on_delete=models.CASCADE,  null=True, blank=True, related_name='lost_matches')
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.tournament.name} - {self.round_number}강 {self.match_number}경기"

    class Meta:
        ordering = ['round_number', 'match_number']