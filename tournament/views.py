from django.shortcuts import render, redirect, get_object_or_404
from .models import Tournament, TournamentMatch
from vote.models import School
from vote.views import update_school_scores
import random
import math
from django.db.models import Count, ExpressionWrapper, F, FloatField, Window
from django.db.models.functions import Rank
from django.core.paginator import Paginator
from django.http import JsonResponse



def get_random_schools_for_tournament(round_of):
    """
    토너먼트 라운드에 맞는 수의 학교를 랜덤하게 선택
    round_of: 4, 8, 16, 32, 64, 128, 256 중 하나
    """
    valid_rounds = [4, 8, 16, 32, 64, 128, 256]
    if round_of not in valid_rounds:
        raise ValueError(f"round_of는 {valid_rounds} 중 하나여야 합니다.")
    
    # 모든 학교 가져오기
    all_schools = list(School.objects.all())
    
    # 전체 학교 수가 필요한 수보다 적으면 에러
    if len(all_schools) < round_of:
        raise ValueError(f"필요한 학교 수({round_of})가 전체 학교 수({len(all_schools)})보다 많습니다.")
    
    # 랜덤하게 선택
    selected_schools = random.sample(all_schools, round_of)
    
    return selected_schools

def create_tournament(request):
    tournament = Tournament.objects.filter(winner__isnull=True).delete()

    if request.method == 'POST':
        round_of = int(request.POST.get('round_of', 16))
        
        # round_of가 0이면 vote_page로 리다이렉트
        if round_of == 0:
            return redirect('vote:vote_page')
            
        try:
            # 랜덤으로 학교 선택
            selected_schools = get_random_schools_for_tournament(round_of)
            
            # 토너먼트 생성
            tournament = Tournament.objects.create(
                name=f"대학 순위 월드컵 {round_of}강",
                total_rounds=round_of,
                current_round=1
            )
            
            # 첫 라운드 매치 생성
            for i in range(0, len(selected_schools), 2):
                if i + 1 < len(selected_schools):
                    TournamentMatch.objects.create(
                        tournament=tournament,
                        round_number=1,
                        match_number=i//2 + 1,
                        school1=selected_schools[i],
                        school2=selected_schools[i+1]
                    )
            
            return redirect('tournament:tournament_detail', tournament_id=tournament.id)
            
        except ValueError as e:
            # 에러 처리
            pass
    return render(request, 'vote/school_list.html')

def tournament_detail(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    # 현재 라운드의 매치들 가져오기
    current_matches = TournamentMatch.objects.filter(
        tournament=tournament,
        round_number=tournament.current_round,
        is_completed=False
    ).order_by('match_number')
    
    # 완료된 매치들 가져오기
    completed_matches = TournamentMatch.objects.filter(
        tournament=tournament,
        round_number=tournament.current_round,
        is_completed=True
    ).order_by('match_number')
    
    # 현재 매치 번호 계산
    current_match_number = completed_matches.count() + 1
    
    # 현재 라운드의 전체 매치 수 계산
    total_matches_in_round = tournament.total_rounds // (2 ** tournament.current_round)
    
    # 토너먼트가 완료되었는지 확인
    is_tournament_completed = tournament.is_completed or (tournament.current_round > math.log2(tournament.total_rounds))
    
    context = {
        'tournament': tournament,
        'current_matches': current_matches,
        'completed_matches': completed_matches,
        'current_match_number': current_match_number,
        'total_matches': total_matches_in_round,
        'is_tournament_completed': is_tournament_completed,
        'round_of': tournament.total_rounds,
    }
    
    return render(request, 'tournament/tournament_detail.html', context)

def tournament_match_result(request, tournament_id, match_id):
    if request.method == 'POST':
        tournament = get_object_or_404(Tournament, id=tournament_id)
        match = get_object_or_404(TournamentMatch, id=match_id)
        
        # 승자 선택
        winner_id = request.POST.get('winner')
        if winner_id == str(match.school1.id):
            match.winner = match.school1
            match.loser = match.school2
        else:
            match.winner = match.school2
            match.loser = match.school1
        match.winner.win_match_count += 1
        match.winner.match_count += 1
        match.loser.match_count += 1
        update_school_scores(match.winner, match.loser)
        match.is_completed = True
        match.save()
        
        # 현재 라운드의 모든 매치가 완료되었는지 확인
        current_round_matches = TournamentMatch.objects.filter(
            tournament=tournament,
            round_number=tournament.current_round
        )
        completed_matches = current_round_matches.filter(is_completed=True)
        
        # 현재 라운드의 모든 매치가 완료되었는지 확인
        if completed_matches.count() == current_round_matches.count():
            # 다음 라운드로 진행
            next_round = tournament.current_round + 1
            
            # 마지막 라운드가 아니면 다음 라운드 매치 생성
            if next_round <= tournament.total_rounds:
                # 이전 라운드의 승자들 가져오기
                winners = TournamentMatch.objects.filter(
                    tournament=tournament,
                    round_number=tournament.current_round,
                    is_completed=True
                ).order_by('match_number').values_list('winner', flat=True)
                
                # 다음 라운드 매치 생성
                match_number = 1
                for i in range(0, len(winners), 2):
                    if i + 1 < len(winners):
                        TournamentMatch.objects.create(
                            tournament=tournament,
                            round_number=next_round,
                            match_number=match_number,
                            school1_id=winners[i],
                            school2_id=winners[i+1]
                        )
                        match_number += 1
                
                # 현재 라운드 업데이트
                tournament.current_round = next_round
                tournament.save()
            else:
                # 토너먼트 완료
                tournament.is_completed = True
                tournament.save()

        if tournament.current_round > math.log2(tournament.total_rounds):
            tournament.winner = match.winner
            tournament.winner.win_tournament_count += 1
            tournament.save()
            tournament.winner.save()

        return redirect('tournament:tournament_detail', tournament_id=tournament.id)


def result(request):
    total_tournaments = Tournament.objects.count()
    schools = School.objects.annotate(
        tournament_win_rate=F('win_tournament_count')*100 / total_tournaments,
        win_rate=F('win_match_count')*100 / F('match_count'),
    ).annotate(
        rank=Window(
            expression=Rank(),
            order_by=('-tournament_win_rate', '-win_rate')
        ),
    ).order_by('-tournament_win_rate', '-win_rate')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        page = int(request.GET.get('page', 1))
        paginator = Paginator(schools, 50)
        
        try:
            schools_page = paginator.page(page)
            schools_data = [{
                'id': school.id,
                'name': school.school_name,
                'score': school.school_score,
                'rank': school.rank,  # 계산된 순위 사용
                'image': school.school_image.url if school.school_image else None,
                'tournament_win_rate': school.tournament_win_rate,
                'win_rate': school.win_rate,
            } for school in schools_page]
            
            return JsonResponse({
                'schools': schools_data,
                'has_next': schools_page.has_next()
            })
        except:
            return JsonResponse({'has_next': False, 'schools': []})

    
    # 초기 로드: 상위 50개만
    initial_schools = schools[:50]
    return render(request, 'tournament/result.html', {'schools': initial_schools})