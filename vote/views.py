from django.shortcuts import render, redirect
from django.db.models import F, Window
from django.db.models.functions import Rank
from django.core.paginator import Paginator
from django.http import JsonResponse
from datetime import date

from .views_vs import get_tier_label
from .models import School, PreviousRank

# -----------------------------
# 오늘 순위 스냅샷 저장
# -----------------------------
def save_today_ranks():
    schools = School.objects.annotate(
        rank=Window(expression=Rank(), order_by=F('rating').desc())
    )
    today = date.today()
    for s in schools:
        PreviousRank.objects.update_or_create(
            school=s,
            date=today,
            defaults={'rank': s.rank}
        )

save_today_ranks()

# -----------------------------
# 대학 순위 페이지
# -----------------------------
def school_list(request):
    # 순위(Rank) 계산
    schools = School.objects.annotate(
        rank=Window(expression=Rank(), order_by=F('rating').desc())
    ).order_by('rank')

    all_schools = list(schools)

    # 어제 스냅샷과 비교해서 변동 계산
    today = date.today()
    yesterday_snapshot = {
        pr.school_id: pr.rank for pr in PreviousRank.objects.filter(date=today)
    }

    for s in schools:
        old_rank = yesterday_snapshot.get(s.id, s.rank)
        s.rank_diff = old_rank - s.rank
        s.rank_diff_abs = abs(s.rank_diff)
        s.tier = get_tier_label(s, all_schools)  # 티어 계산

    # 무한 스크롤 처리
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        page = int(request.GET.get('page', 1))
        paginator = Paginator(schools, 50)
        try:
            schools_page = paginator.page(page)
            schools_data = [{
                'id': school.id,
                'name': school.school_name,
                'score': float(school.rating),
                'rank': school.rank,
                'rank_diff': school.rank_diff,
                'rank_diff_abs': school.rank_diff_abs,  # 추가
                'tier': school.tier,
                'image': school.school_image.url if school.school_image else None,
            } for school in schools_page]
            return JsonResponse({'schools': schools_data, 'has_next': schools_page.has_next()})
        except:
            return JsonResponse({'has_next': False, 'schools': []})

    return render(request, 'vote/school_list.html', {'schools': schools[:50]})

# -----------------------------
# 비교 가능한 학교 추출 (사용 시 참고)
# -----------------------------
def get_comparable_schools(base_school, schools_with_rank):
    current_rank = base_school.rank
    range_limit = 3 if current_rank <= 10 else 5
    return [
        school for school in schools_with_rank
        if school.id != base_school.id and max(1, current_rank - range_limit) <= school.rank <= current_rank + range_limit
    ]

# -----------------------------
# 메인 페이지 리디렉트
# -----------------------------
def redirect_school_list(request):
    return redirect('/', permanent=True)  # 메인 페이지로 리디렉트
