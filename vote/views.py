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


def update_school_scores(winner, loser, k_factor=30):
    # 구간별 대학 리스트와 점수 범위 설정
    tiers = {
        "tier1": {
            "schools": ["서울대학교", "포항공과대학교", "한국과학기술원", "연세대학교", "고려대학교"],
            "min_score": 900,
            "max_score": 1000
        },
        "tier1.5": {
            "schools": ["한국예술종합학교"],
            "min_score": 950,
            "max_score": 850
        },
        "tier2": {
            "schools": ["서강대학교", "성균관대학교", "한양대학교"],
            "min_score": 800,
            "max_score": 899
        },
        "tier2.5": {
            "schools": ["울산과학기술원", "광주과학기술원", "대구경북과학기술원", "서울교육대학교"],
            "min_score": 850,
            "max_score": 750
        },
        "tier3": {
            "schools": ["중앙대학교", "경희대학교", "한국외국어대학교", "서울시립대학교", "이화여자대학교"],
            "min_score": 700,
            "max_score": 799
        },
        "tier3.5": {
            "schools": ["한국에너지공과대학교", "농협대학교"],
            "min_score": 750,
            "max_score": 650
        },
        "tier4": {
            "schools": ["건국대학교", "동국대학교", "홍익대학교"],
            "min_score": 600,
            "max_score": 699
        },
        "tier5": {
            "schools": ["국민대학교", "숭실대학교", "세종대학교", "단국대학교"],
            "min_score": 500,
            "max_score": 599
        },
        "tier6": {
            "schools": ["광운대학교", "명지대학교", "상명대학교", "가톨릭대학교"],
            "min_score": 400,
            "max_score": 499
        },
        "tier7": {
            "schools": ["한성대학교", "서경대학교", "삼육대학교"],
            "min_score": 300,
            "max_score": 399
        },
        
        "tier4~6": {
            "schools": ["부산대학교", "경북대학교", "한국항공대학교", "서울과학기술대학교", "한양대학교 ERICA캠퍼스",
                        "아주대학교", "인하대학교"],
            "min_score": 400,
            "max_score": 699
        },
        "tier5~7": {
            "schools": ["인천대학교", "가천대학교", "경기대학교", "전남대학교", "충남대학교"],
            "min_score": 300,
            "max_score": 599
        },
    }

    def find_tier_info(school_name):
        for tier_num, (tier, info) in enumerate(tiers.items()):
            if school_name in info["schools"]:
                return tier_num, info["min_score"], info["max_score"]
        return None, None, None

    winner_info = find_tier_info(winner.school_name)
    loser_info = find_tier_info(loser.school_name)
    
    # 티어에 속한 대학들의 경우
    if winner_info[0] is not None and loser_info[0] is not None:
        winner_tier, winner_min, winner_max = winner_info
        loser_tier, loser_min, loser_max = loser_info
        
        # ELO 계산
        expected_winner = 1 / (1 + 10**((float(loser.school_score) - float(winner.school_score)) / 400))
        point_change = k_factor * (1 - expected_winner)
        
        # 기본 점수 변동 제한
        max_change = 15.0
        point_change = max(min(point_change, max_change), -max_change)
        
        # 새로운 점수 계산
        new_winner_score = float(winner.school_score) + point_change
        new_loser_score = float(loser.school_score) - point_change
        
        # 승자의 점수가 상한선을 넘는 경우
        if new_winner_score > winner_max and point_change > 0:
            # 상승폭만 극단적으로 감소 (0.1배)
            point_change *= 0.1
            
        # 승자의 점수가 하한선 미만인 경우
        elif new_winner_score < winner_min and point_change < 0:
            # 하락폭만 극단적으로 감소 (0.1배)
            point_change *= 0.1
            
        # 패자의 점수가 상한선을 넘는 경우
        if new_loser_score > loser_max and point_change < 0:
            # 상승폭만 극단적으로 감소 (0.1배)
            point_change *= 0.1
            
        # 패자의 점수가 하한선 미만인 경우
        elif new_loser_score < loser_min and point_change > 0:
            # 하락폭만 극단적으로 감소 (0.1배)
            point_change *= 0.1
            
        # 최종 점수 업데이트
        winner.school_score = float(winner.school_score) + point_change
        loser.school_score = float(loser.school_score) - point_change

    # 티어에 속하지 않은 대학들의 경우 기존 방식 사용
    else:
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
        point_change = adjusted_k * (1 - expected_winner)

        # 점수 업데이트
        loser.school_score = float(loser.school_score) - point_change
        if winner.school_score > 1000:
            point_change * 0.1;
        
        winner.school_score = float(winner.school_score) + point_change

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
    
    # 모든 학교 가져오기
    schools = School.objects.annotate(
        rank=Window(
            expression=Rank(),
            order_by=F('school_score').desc()
        )
    ).order_by('rank')
    
    # 기준이 될 학교 랜덤 선택
    base_school = random.choice(schools)
    
    # 비교 가능한 학교들 가져오기
    comparable_schools = get_comparable_schools(base_school, schools)
    
    # 비교할 학교 랜덤 선택
    if comparable_schools:
        other_school = random.choice(comparable_schools)
    else:
        other_school = random.choice([s for s in schools if s.id != base_school.id])
    
    context = {
        'school1': base_school,
        'school2': other_school,
    }
    return render(request, 'vote/vote_page.html', context)