from django.shortcuts import render, redirect, get_object_or_404
from .models import School
import requests
from django.contrib import messages
from django.db.models import Avg
import random

# Create your views here.

api_key = "dfac745a466d279dd3fcbc6c6dda4483"
url = "https://www.career.go.kr/cnet/openapi/getOpenApi?apiKey={}&svcType=api&svcCode=SCHOOL&contentType=json&gubun=univ_list&perPage=1000".format(api_key)
response = requests.get(url)
data = response.json()


def school_list(request):
     # 총 400개의 대학교가 있음
    schools = School.objects.all().order_by('-school_score')

    li = [school.school_score for school in schools]
    scores = []

    num = 0
    tf = 0
    
    # 학교 순위를 지정해주는 반복문 -> 동일 점수 시 같은 순위 부여
    for i in range(399):
        if(li[i] == li[i+1]):
            scores.append(num+1)
            tf += 1
        else:
            scores.append(num+1)
            num += 1 + tf
            tf = 0
    scores.append(num+1)

    """ 학교리스트 생성코드
    for item in data['dataSearch']['content']:
        existing_school = School.objects.filter(school_name=item['schoolName']).first()

        if existing_school is None:
            new_school = School(school_name=item['schoolName'], school_address=item['adres'])
            new_school.save()
        else:
            continue
    """

    myzip = zip(schools, scores)
    return render(request, 'vote/school_list.html', {'myzip': myzip})


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
        
        # 선택된 학교와 선택되지 않은 학교의 점수 업데이트
        winner = School.objects.get(id=winner_id)
        loser = School.objects.get(id=loser_id)
        
        winner.school_score += 1
        loser.school_score -= 1
        
        winner.save()
        loser.save()
        
        return redirect('vote:vote_page')
    
    # 랜덤하게 두 개의 학교 선택
    schools = list(School.objects.all())
    if len(schools) < 2:
        return render(request, 'vote/error.html', {'message': '학교가 충분하지 않습니다.'})
    
    selected_schools = random.sample(schools, 2)
    
    context = {
        'school1': selected_schools[0],
        'school2': selected_schools[1],
    }
    return render(request, 'vote/vote_page.html', context)  