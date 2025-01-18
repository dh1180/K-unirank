from django.shortcuts import render, redirect, get_object_or_404
from .models import School
import requests
from django.db.models import F, Window
from django.db.models.functions import Rank, DenseRank
import random
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Count, Case, When, Value, IntegerField

# Create your views here.

api_key = "dfac745a466d279dd3fcbc6c6dda4483"
url = "https://www.career.go.kr/cnet/openapi/getOpenApi?apiKey={}&svcType=api&svcCode=SCHOOL&contentType=json&gubun=univ_list&perPage=1000".format(api_key)
response = requests.get(url)
data = response.json()


def school_list(request):
    # DenseRank를 사용하여 동점자 처리
    schools = School.objects.annotate(
        rank=Window(
            expression=Rank(),
            order_by=F('school_score').desc()
        )
    ).order_by('rank')
    
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
            } for school in schools_page]
            
            return JsonResponse({
                'schools': schools_data,
                'has_next': schools_page.has_next()
            })
        except:
            return JsonResponse({'has_next': False, 'schools': []})
    
    # 초기 로드: 상위 50개만
    initial_schools = schools[:50]
    return render(request, 'vote/school_list.html', {'schools': initial_schools})


def upload(request):
    schools = School.objects.all().order_by('-school_score')
    if request.method == 'POST':
        school = request.POST['school']
        selected_school = School.objects.filter(school_name=school).first()
        if "image" in request.FILES:
            selected_school.school_image = request.FILES["image"]
            selected_school.save()

        return redirect('vote:upload')

    context = {
        'schools': schools,
        'is_superuser': request.user.is_superuser
    }
    return render(request, 'vote/upload.html', context)


def susi_pdf_upload(request):
    schools = School.objects.all().order_by('-school_score')
    if request.method == 'POST':
        school = request.POST['school']
        selected_school = School.objects.filter(school_name=school).first()

        selected_school.susi_school_pdf = request.FILES["susi"]
        selected_school.save()

        return redirect('vote:susi_pdf_upload')

    context = {
        'schools': schools,
        'is_superuser': request.user.is_superuser
    }
    return render(request, 'vote/susi_pdf_upload.html', context)  


def jungsi_pdf_upload(request):
    schools = School.objects.all().order_by('-school_score')
    if request.method == 'POST':
        school = request.POST['school']
        selected_school = School.objects.filter(school_name=school).first()

        selected_school.jungsi_school_pdf = request.FILES["jungsi"]
        selected_school.save()

        return redirect('vote:jungsi_pdf_upload')

    context = {
        'schools': schools,
        'is_superuser': request.user.is_superuser
    }
    return render(request, 'vote/jungsi_pdf_upload.html', context)  


def update_school_scores(winner, loser, k_factor=16):
    # 순위 차이와 점수 차이 계산
    rank_diff = winner.rank - loser.rank
    score_diff = float(winner.school_score) - float(loser.school_score)
    
    # 순위와 점수 차이를 고려한 k_factor 조정
    if rank_diff > 0:  # 낮은 순위가 이겼을 때
        score_weight = abs(score_diff) / 20
        adjusted_k = k_factor * (1.0 + rank_diff/20 + score_weight)
    elif rank_diff < 0:  # 높은 순위가 이겼을 때
        score_weight = abs(score_diff) / 20
        adjusted_k = k_factor * (1.0 / (1 + abs(rank_diff)/10 + score_weight))
    else:  # 같은 순위끼리 겨룰 때
        score_weight = abs(score_diff) / 20
        adjusted_k = k_factor * (1.0 + score_weight)
    
    # 최대 k_factor 제한
    adjusted_k = min(adjusted_k, k_factor * 2)
    
    # ELO 계산
    expected_winner = 1 / (1 + 10**((float(loser.school_score) - float(winner.school_score)) / 400))
    
    # 점수 변동 계산 및 제한
    point_change = adjusted_k * (1 - expected_winner)
    max_change = 15.0
    point_change = max(min(point_change, max_change), -max_change)
    
    # 점수 업데이트
    winner.school_score = float(winner.school_score) + point_change
    loser.school_score = float(loser.school_score) - point_change
    
    winner.save()
    loser.save()

def get_comparable_schools(base_school, schools_with_rank):
    current_rank = base_school.rank
    
    # 구간별 범위 설정
    if current_rank <= 10:
        range_limit = 3
    else:
        range_limit = 5
    
    # 먼저 범위에 맞는 학교들을 필터링
    comparable_schools = [
        school for school in schools_with_rank
        if school.id != base_school.id
        and max(1, current_rank - range_limit) <= school.rank <= current_rank + range_limit
    ]
    
    return comparable_schools

def get_school_rank(school):
    # 해당 학교보다 점수가 높은 학교 수를 세서 순위 계산
    higher_scores = School.objects.filter(
        school_score__gt=school.school_score
    ).count()
    return higher_scores + 1

def vote_page(request):
    if request.method == 'POST':
        winner_id = request.POST.get('selected_school')
        loser_id = request.POST.get('other_school')
        
        # 기본 정보 가져오기
        winner = School.objects.get(id=winner_id)
        loser = School.objects.get(id=loser_id)
        
        # 순위 계산
        winner.rank = get_school_rank(winner)
        loser.rank = get_school_rank(loser)
        
        update_school_scores(winner, loser)
        return redirect('vote:vote_page')
    
    #순위를 포함한 학교 목록 가져오기
    schools_with_rank = School.objects.annotate(
        rank=Window(
            expression=Rank(),
            order_by=F('school_score').desc()
        )
    )
    
    # 랜덤으로 첫 번째 학교 선택
    school1 = random.choice(schools_with_rank)
    
    # school1의 순위 기준으로 비교 가능한 학교들 필터링
    nearby_schools = get_comparable_schools(school1, schools_with_rank)
    
    if len(nearby_schools) > 0:
        school2 = random.choice(nearby_schools)
    else:
        # 근처에 학교가 없으면 다른 학교 랜덤 선택
        school2 = random.choice(schools_with_rank.exclude(id=school1.id))
    
    context = {
        'school1': school1,
        'school2': school2,
    }
    return render(request, 'vote/vote_page.html', context)  
