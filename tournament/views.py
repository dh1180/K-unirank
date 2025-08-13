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
# Glicko-2 상수 및 함수 (정식 μ–φ 일관)
# -----------------------------
Q = math.log(10) / 400.0
TAU = 0.5
BASE_RATING = 1500.0
SCALER = 173.7178  # = 400 / ln(10)
EPS = 1e-6        # 수치 안정화용

def to_mu_phi(rating, rd):
    """레이팅/ RD 를 μ/φ 로 변환"""
    mu = (rating - BASE_RATING) / SCALER
    phi = rd / SCALER
    return mu, phi

def from_mu_phi(mu, phi):
    """μ/φ 를 레이팅/RD 로 변환"""
    rating = BASE_RATING + SCALER * mu
    rd = SCALER * phi
    return rating, rd

def g(phi):
    # Glicko-2 (μ–φ 공간) 정식: q 제거
    return 1.0 / math.sqrt(1.0 + (3.0 * (phi ** 2)) / (math.pi ** 2))

def expected_score(mu, mu_op, phi_op):
    x = g(phi_op) * (mu - mu_op)
    if x > 35: return 1.0
    if x < -35: return 0.0
    return 1.0 / (1.0 + math.exp(-x))

def volatility_update(sigma, delta, v, phi, tau=TAU):
    """
    표준 논문(시스템 2) 방식의 σ 업데이트 (μ/φ 스페이스).
    a = ln(σ^2), 이분+뉴턴 혼합 루틴.
    """
    a = math.log(sigma ** 2)
    A = a
    # f(x) 정의
    def f(x):
        ex = math.exp(x)
        num = ex * (delta ** 2 - phi ** 2 - v - ex)
        den = 2.0 * (phi ** 2 + v + ex) ** 2
        return (num / den) - ((x - A) / (tau ** 2))

    # B 초기값 선택
    if delta ** 2 > (phi ** 2 + v):
        B = math.log(delta ** 2 - phi ** 2 - v)
    else:
        k = 1
        B = A - k * tau
        while f(B) < 0:
            k += 1
            B = A - k * tau

    # 이분 + 이터레이션
    fA = f(A)
    fB = f(B)
    while abs(B - A) > 1e-6:
        C = A + (A - B) * fA / (fB - fA)
        fC = f(C)
        if fC * fB < 0:
            A, fA = B, fB
        else:
            fA = fA / 2.0
        B, fB = C, fC

    return math.exp(A / 2.0)

def glicko_update(player, opponents, results):
    """
    표준 Glicko-2 단일 기간 업데이트 (μ/φ 일관).
    - player: (rating, RD, sigma)
    - opponents: [(op_rating, op_rd), ...]
    - results: [1/0, ...]  (승=1, 패=0)
    ※ 라운드 가중치/300점 완화 제거(정확도 향상)
    """
    rating, rd, sigma = player
    mu, phi = to_mu_phi(rating, rd)

    # v^{-1} = Σ g^2 E(1−E)   (여기서 q^2 추가하지 않음 — μ/φ 스페이스)
    v_inv = 0.0
    delta_sum = 0.0
    for (op_rating, op_rd), result in zip(opponents, results):
        mu_op, phi_op = to_mu_phi(op_rating, op_rd)
        E = expected_score(mu, mu_op, phi_op)
        E = min(max(E, EPS), 1.0 - EPS)  # 안정화
        g_phi = g(phi_op)
        v_inv += (g_phi ** 2) * E * (1.0 - E)
        delta_sum += g_phi * (result - E)

    if v_inv <= 0:
        # 상대가 없거나 수치적 문제 — 변화 없음
        return rating, rd, sigma

    v = 1.0 / v_inv
    # Δ = v * Σ g(φ)(s − E)   (여기서 q 제거 — μ/φ 스페이스)
    delta = v * delta_sum

    sigma_prime = volatility_update(sigma, delta, v, phi, tau=TAU)

    # 사전 RD 증가(프리-RD)
    phi_star = math.sqrt(phi ** 2 + sigma_prime ** 2)

    # φ' = 1 / sqrt(1/φ_*^2 + 1/v)
    phi_prime = 1.0 / math.sqrt((1.0 / (phi_star ** 2)) + (1.0 / v))

    # μ' = μ + φ'^2 * Σ g(φ)(s − E)
    mu_prime = mu + (phi_prime ** 2) * delta_sum

    R_new, RD_new = from_mu_phi(mu_prime, phi_prime)
    return R_new, RD_new, sigma_prime

def update_school_scores(winner, loser, match):
    # 경기 시작 전 로그
    logging.info(
        f"[ROUND {match.round_number}] Match {match.match_number} START - "
        f"Winner({winner.school_name}) Rating={winner.rating:.2f}, "
        f"Loser({loser.school_name}) Rating={loser.rating:.2f}"
    )

    # Glicko-2 점수 계산 (정식 μ–φ)
    new_winner_rating, new_winner_rd, new_winner_sigma = glicko_update(
        (winner.rating, winner.rd, winner.volatility),
        [(loser.rating, loser.rd)], [1]
    )
    new_loser_rating, new_loser_rd, new_loser_sigma = glicko_update(
        (loser.rating, loser.rd, loser.volatility),
        [(winner.rating, winner.rd)], [0]
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
# 티어 기반 랜덤 참가자 선정 (기존 유지)
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

    # 🔧 final_score = rating (이중 집계 제거)
    schools = School.objects.annotate(
        final_score=ExpressionWrapper(
            F('rating'),
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
                'final_score': float(school.final_score),  # = rating
                'tournament_win_rate': float(school.tournament_win_rate),
                'win_rate': float(school.win_rate),
                'win_tournament_count': school.win_tournament_count,
                'win_match_count': school.win_match_count
            } for school in schools_page]
            return JsonResponse({'schools': schools_data, 'has_next': schools_page.has_next()})
        except Exception:
            return JsonResponse({'schools': [], 'has_next': False})

    return render(request, 'tournament/result.html', {'schools': ranked_schools[:50]})
