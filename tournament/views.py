import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import F, FloatField, ExpressionWrapper, Value
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.http import JsonResponse
from datetime import timedelta
import random, math

from .models import Tournament, TournamentMatch
from vote.models import School

# -----------------------------
# 로깅 설정
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),  # 콘솔 출력
        logging.FileHandler("tournament_scores.log", encoding="utf-8")  # 파일 저장
    ]
)

# -----------------------------
# Glicko-2 상수 및 함수
# -----------------------------
Q = math.log(10) / 400
TAU = 0.5
BASE_RATING = 1500
SCALER = 173.7178

def g(rd):
    return 1 / math.sqrt(1 + (3 * (Q ** 2) * (rd ** 2)) / (math.pi ** 2))

def expected_score(r, r_op, rd_op):
    return 1 / (1 + math.exp(-g(rd_op) * (r - r_op)))

def volatility_update(sigma, delta, v, phi, a=None, tau=TAU):
    if a is None:
        a = math.log(sigma ** 2)
    A = a
    epsilon = 0.000001

    def f(x):
        exp_x = math.exp(x)
        num = exp_x * (delta ** 2 - phi ** 2 - v - exp_x)
        denom = 2 * (phi ** 2 + v + exp_x) ** 2
        return (num / denom) - ((x - A) / (tau ** 2))

    B = A
    if delta ** 2 > phi ** 2 + v:
        B = math.log(delta ** 2 - phi ** 2 - v)
    k = 0
    while abs(B - A) > epsilon and k < 50:
        k += 1
        fA, fB = f(A), f(B)
        B = A + ((A - B) * fA) / (fB - fA)
    return math.exp(A / 2)

def get_round_weight(round_number, total_rounds):
    max_round = int(math.log2(total_rounds))
    min_w, max_w = 0.8, 1.5
    if max_round == 1:
        return max_w
    return min_w + (max_w - min_w) * ((round_number - 1) / (max_round - 1))

def glicko_update(player, opponents, results, round_number=1, total_rounds=16):
    rating, RD, sigma = player
    mu = (rating - BASE_RATING) / SCALER
    phi = RD / SCALER

    v_inv, delta_sum = 0, 0
    for (op_rating, op_rd), result in zip(opponents, results):
        mu_op = (op_rating - BASE_RATING) / SCALER
        phi_op = op_rd / SCALER
        E = expected_score(mu, mu_op, phi_op)
        g_phi = g(phi_op)
        v_inv += (Q ** 2) * (g_phi ** 2) * E * (1 - E)
        delta_sum += g_phi * (result - E)

    v = 1 / v_inv
    delta = v * delta_sum * Q

    sigma_prime = volatility_update(sigma, delta, v, phi)
    phi_star = math.sqrt(phi ** 2 + sigma_prime ** 2)
    phi_prime = 1 / math.sqrt((1 / phi_star ** 2) + (1 / v))
    mu_prime = mu + (phi_prime ** 2) * delta_sum * Q

    R_new = BASE_RATING + SCALER * mu_prime
    RD_new = phi_prime * SCALER

    weight = get_round_weight(round_number, total_rounds)
    R_new = rating + (R_new - rating) * weight

    if opponents:
        avg_op_rating = sum(op_rating for op_rating, _ in opponents) / len(opponents)
        if abs(rating - avg_op_rating) > 300:
            R_new = rating + (R_new - rating) * 0.5

    return R_new, RD_new, sigma_prime

def update_school_scores(winner, loser, match):
    total_rounds = match.tournament.total_rounds

    # 경기 시작 전 로그
    logging.info(
        f"[ROUND {match.round_number}] Match {match.match_number} START - "
        f"Winner({winner.school_name}) Rating={winner.rating:.2f}, "
        f"Loser({loser.school_name}) Rating={loser.rating:.2f}"
    )

    # Glicko-2 점수 계산
    new_winner_rating, new_winner_rd, new_winner_sigma = glicko_update(
        (winner.rating, winner.rd, winner.volatility),
        [(loser.rating, loser.rd)], [1],
        round_number=match.round_number,
        total_rounds=total_rounds
    )
    new_loser_rating, new_loser_rd, new_loser_sigma = glicko_update(
        (loser.rating, loser.rd, loser.volatility),
        [(winner.rating, winner.rd)], [0],
        round_number=match.round_number,
        total_rounds=total_rounds
    )

    # 새 점수 적용
    winner.rating, winner.rd, winner.volatility = new_winner_rating, new_winner_rd, new_winner_sigma
    loser.rating, loser.rd, loser.volatility = new_loser_rating, new_loser_rd, new_loser_sigma

    # 경기 횟수 기록
    winner.win_match_count += 1
    winner.match_count += 1
    loser.match_count += 1
    winner.save()
    loser.save()

    # 경기 종료 후 로그
    logging.info(
        f"[ROUND {match.round_number}] Match {match.match_number} END - "
        f"Winner({winner.school_name}) New Rating={winner.rating:.2f}, "
        f"Loser({loser.school_name}) New Rating={loser.rating:.2f}"
    )

# -----------------------------
# 티어 기반 랜덤 참가자 선정
# -----------------------------
def select_random_schools(round_of):
    all_schools = list(School.objects.order_by('-rating'))
    total = len(all_schools)
    if total < round_of:
        return all_schools

    tiers = {'S': [], 'A': [], 'B': [], 'C': [], 'D': [], 'F': []}
    for i, s in enumerate(all_schools):
        if i < int(total * 0.02): tiers['S'].append(s)
        elif i < int(total * 0.10): tiers['A'].append(s)
        elif i < int(total * 0.30): tiers['B'].append(s)
        elif i < int(total * 0.60): tiers['C'].append(s)
        elif i < int(total * 0.90): tiers['D'].append(s)
        else: tiers['F'].append(s)

    ratios = {'S':0.10,'A':0.20,'B':0.30,'C':0.20,'D':0.15,'F':0.05}
    selected, remaining = [], round_of

    for t, ratio in ratios.items():
        count = min(len(tiers[t]), int(round_of * ratio))
        if count > 0:
            selected += random.sample(tiers[t], count)
            remaining -= count

    if remaining > 0:
        pool = [s for s in all_schools if s not in selected]
        selected += random.sample(pool, remaining)

    random.shuffle(selected)
    return selected

def get_tier_label(school, all_schools):
    sorted_list = sorted(all_schools, key=lambda s: s.rating, reverse=True)
    idx, total = sorted_list.index(school), len(sorted_list)
    if idx < int(total * 0.02): return 'S'
    elif idx < int(total * 0.10): return 'A'
    elif idx < int(total * 0.30): return 'B'
    elif idx < int(total * 0.60): return 'C'
    elif idx < int(total * 0.90): return 'D'
    return 'F'

# -----------------------------
# 토너먼트 뷰
# -----------------------------
def cleanup_abandoned_tournaments():
    expiration = timezone.now() - timedelta(hours=2)
    Tournament.objects.filter(is_completed=False, created_at__lt=expiration).delete()

def create_tournament(request):
    Tournament.objects.filter(winner__isnull=True).delete()
    if request.method == 'POST':
        round_of = int(request.POST.get('round_of', 16))
        if round_of == 0:
            return redirect('vote:vote_page')

        selected = select_random_schools(round_of)
        selected.sort(key=lambda x: x.rating, reverse=True)

        top_half = selected[:round_of//2]
        bottom_half = selected[round_of//2:]
        random.shuffle(top_half)
        random.shuffle(bottom_half)

        pairs = []
        for t, b in zip(top_half, bottom_half):
            pairs.append((t, b) if random.random() < 0.5 else (b, t))
        random.shuffle(pairs)

        tournament = Tournament.objects.create(
            name=f"대학 순위 월드컵 {round_of}강",
            total_rounds=round_of,
            current_round=1
        )
        for i, (s1, s2) in enumerate(pairs, start=1):
            TournamentMatch.objects.create(
                tournament=tournament,
                round_number=1,
                match_number=i,
                school1=s1,
                school2=s2
            )
        return redirect('tournament:tournament_detail', tournament_id=tournament.id)
    return render(request, 'vote/school_list.html')

def tournament_detail(request, tournament_id):
    cleanup_abandoned_tournaments()
    tournament = get_object_or_404(Tournament, id=tournament_id)

    current_match = TournamentMatch.objects.filter(
        tournament=tournament, round_number=tournament.current_round, is_completed=False
    ).select_related('school1', 'school2').order_by('match_number').first()

    all_schools = list(School.objects.all())
    if current_match:
        current_match.school1.tier = get_tier_label(current_match.school1, all_schools)
        current_match.school2.tier = get_tier_label(current_match.school2, all_schools)

    completed = TournamentMatch.objects.filter(tournament=tournament, round_number=tournament.current_round, is_completed=True)
    current_number = completed.count() + 1
    total_matches = tournament.total_rounds // (2 ** tournament.current_round)

    return render(request, 'tournament/tournament_detail.html', {
        'tournament': tournament,
        'current_match': current_match,
        'current_match_number': current_number,
        'total_matches': total_matches,
        'is_tournament_completed': tournament.is_completed,
        'round_of': tournament.total_rounds,
    })

def tournament_match_result(request, tournament_id, match_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    match = get_object_or_404(TournamentMatch, id=match_id)

    if request.method == 'POST':
        winner_id = request.POST.get('winner')
        match.winner, match.loser = (
            (match.school1, match.school2) if winner_id == str(match.school1.id) else (match.school2, match.school1)
        )
        update_school_scores(match.winner, match.loser, match)
        match.is_completed = True
        match.save()

        current_round_matches = TournamentMatch.objects.filter(
            tournament=tournament, round_number=tournament.current_round
        )

        if current_round_matches.filter(is_completed=True).count() == current_round_matches.count():
            next_round = tournament.current_round + 1
            winners = list(TournamentMatch.objects.filter(
                tournament=tournament, round_number=tournament.current_round, is_completed=True
            ).order_by('match_number').values_list('winner', flat=True))

            if len(winners) > 1:
                for i in range(0, len(winners) - 1, 2):
                    TournamentMatch.objects.create(
                        tournament=tournament,
                        round_number=next_round,
                        match_number=i // 2 + 1,
                        school1_id=winners[i],
                        school2_id=winners[i + 1]
                    )
                tournament.current_round = next_round
                tournament.save()
            else:
                tournament.winner_id = winners[0]
                tournament.is_completed = True
                tournament.winner.win_tournament_count += 1
                tournament.winner.save()
                tournament.save()

        return redirect('tournament:tournament_detail', tournament_id=tournament.id)

def result(request):
    total_tournaments = Tournament.objects.filter(is_completed=True).count() or 1

    schools = School.objects.annotate(
        final_score=ExpressionWrapper(
            F('rating') + (F('win_tournament_count') * 50) + (F('win_match_count') * 5),
            output_field=FloatField()
        ),
        tournament_win_rate=ExpressionWrapper(
            (F('win_tournament_count') * 100.0) / total_tournaments,
            output_field=FloatField()
        ),
        win_rate=ExpressionWrapper(
            Coalesce((F('win_match_count') * 100.0) / F('match_count'), Value(0.0)),
            output_field=FloatField()
        )
    ).order_by('-final_score')

    ranked_schools = []
    for idx, school in enumerate(schools, start=1):
        school.rank = idx
        ranked_schools.append(school)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        page = int(request.GET.get('page', 1))
        paginator = Paginator(ranked_schools, 50)
        try:
            schools_page = paginator.page(page)
            schools_data = [{
                'rank': school.rank,
                'id': school.id,
                'name': school.school_name,
                'image': school.school_image.url if school.school_image else None,
                'rating': float(school.rating),
                'final_score': float(school.final_score),
                'tournament_win_rate': float(school.tournament_win_rate),
                'win_rate': float(school.win_rate),
                'win_tournament_count': school.win_tournament_count,
                'win_match_count': school.win_match_count
            } for school in schools_page]
            return JsonResponse({'schools': schools_data, 'has_next': schools_page.has_next()})
        except:
            return JsonResponse({'schools': [], 'has_next': False})

    return render(request, 'tournament/result.html', {'schools': ranked_schools[:50]})
