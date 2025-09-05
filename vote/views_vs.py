# views.py
import math
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import F, Value
from django.db.models.functions import Abs

from vote.models import School

# -----------------------------
# Glicko-2 (필요부분만)
# -----------------------------
Q = math.log(10) / 400
TAU = 0.5
BASE_RATING = 1500
SCALER = 173.7178

def g(rd):
    return 1 / math.sqrt(1 + (3 * (Q**2) * (rd**2)) / (math.pi**2))

def expected_score(r, r_op, rd_op):
    return 1 / (1 + math.exp(-g(rd_op) * (r - r_op)))

def volatility_update(sigma, delta, v, phi, a=None, tau=TAU):
    if a is None: a = math.log(sigma ** 2)
    A, eps = a, 1e-6
    def f(x):
        ex = math.exp(x)
        num = ex * (delta**2 - phi**2 - v - ex)
        den = 2 * (phi**2 + v + ex) ** 2
        return (num / den) - ((x - A) / (tau**2))
    B = math.log(delta**2 - phi**2 - v) if delta**2 > phi**2 + v else A
    for _ in range(50):
        if abs(B - A) <= eps: break
        fA, fB = f(A), f(B)
        B = A + ((A - B) * fA) / (fB - fA)
    return math.exp(A / 2)

def glicko_update(player, opponents, results, round_weight=1.0):
    rating, RD, sigma = player
    mu, phi = (rating - BASE_RATING) / SCALER, RD / SCALER

    v_inv, delta_sum = 0.0, 0.0
    for (op_rating, op_rd), result in zip(opponents, results):
        mu_op, phi_op = (op_rating - BASE_RATING) / SCALER, op_rd / SCALER
        E = expected_score(mu, mu_op, phi_op)
        g_phi = g(phi_op)
        v_inv += (Q**2) * (g_phi**2) * E * (1 - E)
        delta_sum += g_phi * (result - E)

    v = 1 / v_inv
    delta = v * delta_sum * Q

    sigma_p = volatility_update(sigma, delta, v, phi)
    phi_star = math.sqrt(phi**2 + sigma_p**2)
    phi_p = 1 / math.sqrt((1 / phi_star**2) + (1 / v))
    mu_p = mu + (phi_p**2) * delta_sum * Q

    R_new = BASE_RATING + SCALER * mu_p
    RD_new = phi_p * SCALER

    # 토너먼트가 없으니 간단히 라운드 가중치만 유지(기본 1.0)
    R_new = rating + (R_new - rating) * round_weight
    return R_new, RD_new, sigma_p

# -----------------------------
# 유틸: 랜덤 + 가장가까운 한 개
# -----------------------------
def get_random_and_closest_school():
    s1 = School.objects.order_by("?").first()
    if not s1:
        return None, None
    s2 = (
        School.objects
        .exclude(id=s1.id)
        .annotate(score_diff=Abs(F("rating") - Value(s1.rating)))
        .order_by("score_diff")
        .first()
    )
    return s1, s2

def get_tier_label(school, all_schools):
    sorted_list = sorted(all_schools, key=lambda s: s.rating, reverse=True)
    idx, total = sorted_list.index(school), len(sorted_list)
    if idx < int(total * 0.02): return "S"
    elif idx < int(total * 0.10): return "A"
    elif idx < int(total * 0.30): return "B"
    elif idx < int(total * 0.60): return "C"
    elif idx < int(total * 0.90): return "D"
    return "F"

def infinite_vs_view(request):
    if request.method == "POST":
        # 선택 결과 반영
        selected_id = request.POST.get("selected_school")
        other_id    = request.POST.get("other_school")
        if selected_id and other_id:
            win = get_object_or_404(School, pk=selected_id)
            lose = get_object_or_404(School, pk=other_id)

            # 한 번의 매치로 간단 업데이트(가중치 1.0)
            win.rating, win.rd, win.volatility = glicko_update(
                (win.rating, win.rd, win.volatility),
                [(lose.rating, lose.rd)], [1],
                round_weight=1.0
            )
            lose.rating, lose.rd, lose.volatility = glicko_update(
                (lose.rating, lose.rd, lose.volatility),
                [(win.rating, win.rd)], [0],
                round_weight=1.0
            )

            # 선택: 카운터가 있으면 갱신
            if hasattr(win, "win_match_count"): win.win_match_count += 1
            if hasattr(win, "match_count"):     win.match_count += 1
            if hasattr(lose, "match_count"):    lose.match_count += 1

            win.save(); lose.save()

            print(
                f"VS 결과: {win.school_name}({win.rating:.1f}) 승리 / "
                f"{lose.school_name}({lose.rating:.1f}) 패배"
            )

        # PRG: 새 매치 보이도록 GET으로 리다이렉트
        return redirect("vote:vote_page")

    # GET: 새 매치 보여주기
    s1, s2 = get_random_and_closest_school()
    if not s1 or not s2:
        return render(request, "vote/match.html", {"error": "학교 데이터가 없습니다."})

    all_ = list(School.objects.only("id", "rating").order_by("-rating"))
    context = {
        "school1": s1,
        "school2": s2,
        "school1_tier": get_tier_label(s1, all_),
        "school2_tier": get_tier_label(s2, all_),
        "title": "대학순위 무한 VS",
    }
    return render(request, "vote/vote_page.html", context)
