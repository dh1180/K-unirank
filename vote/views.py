from django.shortcuts import render, redirect, get_object_or_404
from .models import School, School_score
import requests
from django.contrib import messages
from django.db.models import Avg

# Create your views here.

api_key = "dfac745a466d279dd3fcbc6c6dda4483"
url = "https://www.career.go.kr/cnet/openapi/getOpenApi?apiKey={}&svcType=api&svcCode=SCHOOL&contentType=json&gubun=univ_list&perPage=1000".format(api_key)
response = requests.get(url)
data = response.json()


def school_list(request):
     # 총 400개의 대학교가 있음
    school_average_score = School.objects.annotate(average_score=Avg('school_score__individual_score'))
    schools = school_average_score.order_by('-average_score')

    li = [school.get_average_score() for school in schools]
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
    if request.user.is_authenticated:
        voted_school = School.objects.filter(voted_users=request.user)
        myzip = zip(schools, scores)
        return render(request, 'vote/school_list.html', {'myzip': myzip, 'voted_school': voted_school})

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


def has_duplicates(school_list):
    without_duplicates = [value for value in school_list if value != '']
    return len(without_duplicates) == len(set(without_duplicates))


def school_score(request):
    schools = School.objects.all()
    if request.method == 'POST':
        date = request.POST.getlist('school_name[]')
        if has_duplicates(date):
            count = 0
            for school_name in date:
                school = School.objects.filter(school_name=school_name).first()
                if school is not None:
                    if school.voted_users.filter(pk=request.user.pk).exists():
                        messages.info(request, "이미 순위를 투표한 대학교를 선택하셨습니다.")
                        return redirect('vote:school_score')
                    else:
                        school.voted_users.add(request.user)
                    school_score = School_score()
                    school_score.school = school
                    school_score.voted_user = request.user
                    school_score.individual_score = (401-count)
                    school_score.save()
                count += 1
            return redirect('vote:school_list')
        else:
            messages.info(request, "중복된 대학교를 선택하셨습니다.")
            return redirect('vote:school_score')
    return render(request, 'vote/school_score.html', {'schools': schools})


def upload(request):
    school_average_score = School.objects.annotate(average_score=Avg('school_score__individual_score'))
    schools = school_average_score.order_by('average_score')
    if request.method == 'POST':
        school = request.POST['school']
        selected_school = School.objects.filter(school_name=school).first()
        if "image" in request.FILES:
            selected_school.school_image = request.FILES["image"]
            selected_school.save()

        return redirect('vote:upload')
    return render(request, 'vote/upload.html', {'schools': schools})


def user_voted(request):
    school_average_score = School_score.objects.annotate(average_score=Avg('individual_score'))
    voted_school = school_average_score.filter(voted_user=request.user).order_by('-average_score')
    not_voted_school = School.objects.exclude(voted_users=request.user)
    return render(request, 'vote/user_voted.html', {'voted_school': voted_school, 'not_voted_school': not_voted_school})


def vote_delete(request, school_pk, school_score_pk):
    if request.user.is_authenticated:
        school_score = get_object_or_404(School_score, pk=school_score_pk)
        school = get_object_or_404(School, pk=school_pk)
        if request.user == school_score.voted_user:
            school_score.delete()
            school.voted_users.remove(request.user)
    return redirect('vote:user_voted')


def user_delete(request):
    if request.method == 'POST':
        request.user.delete()
        return redirect('vote:school_list')
    return render(request, 'vote/school_list.html')