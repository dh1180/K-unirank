from django.shortcuts import render, redirect, get_object_or_404
from .models import School
import requests
from django.db.models import F, Window
from django.db.models.functions import Rank, DenseRank
import random
from django.core.paginator import Paginator
from django.http import JsonResponse

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


def vote_page(request):
    if request.method == 'POST':
        winner_id = request.POST.get('selected_school')
        loser_id = request.POST.get('other_school')
        
        winner = School.objects.get(id=winner_id)
        loser = School.objects.get(id=loser_id)
        
        winner.school_score += 1
        loser.school_score -= 1
        
        winner.save()
        loser.save()
        
        return redirect('vote:vote_page')
    
    # 순위를 포함한 학교 목록 가져오기
    schools_with_rank = School.objects.annotate(
        rank=Window(
            expression=Rank(),
            order_by=F('school_score').desc()
        )
    )
    
    # 랜덤으로 첫 번째 학교 선택
    school1 = random.choice(schools_with_rank)
    school1_rank = school1.rank
    
    # school1의 순위 기준으로 위아래 5개씩의 학교들 필터링
    nearby_schools = schools_with_rank.filter(
        rank__gte=max(1, school1_rank - 5),  # 1순위보다 작아지지 않도록
        rank__lte=school1_rank + 5
    ).exclude(id=school1.id)
    
    if nearby_schools.exists():
        school2 = random.choice(nearby_schools)
    else:
        # 근처에 학교가 없으면 다른 학교 랜덤 선택
        school2 = random.choice(schools_with_rank.exclude(id=school1.id))
    
    context = {
        'school1': school1,
        'school2': school2,
    }
    return render(request, 'vote/vote_page.html', context)  