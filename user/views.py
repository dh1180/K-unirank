from community.models import Post, Comment
from vote.models import School
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
import requests, json


def user_profile(request):
    return render(request, 'user/user_profile.html')


def user_posts(request):
    posts = Post.objects.filter(author=request.user).order_by('-date')
    page_number = request.GET.get('page')
    today = timezone.now().date()

    paginator = Paginator(posts, 16)
    page_obj = paginator.get_page(page_number)
    return render(request, 'user/user_posts.html', {'page_obj': page_obj, 'today': today})


def change_username(request):
    present_user = request.user
    if present_user.is_authenticated:
        if request.method == 'POST':
            is_user_exist = User.objects.filter(username=request.POST["username"])
            if is_user_exist.exists():
                # 일치하는 사용자가 존재하는 경우
                return render(request, 'user/user_profile.html', {'error': '같은 이름의 사용자가 존재합니다.'})
            else:
                present_user.username = request.POST["username"]
                present_user.save()
            return render(request, 'user/user_profile.html')
        return render(request, 'user/user_profile.html')
    else:
        return render(request, 'user/user_profile.html', {'error': '사용자가 로그인하지 않았습니다.'})


def user_comment_posts(request):
    comment_posts = Comment.objects.filter(author=request.user).order_by('-date')
    page_number = request.GET.get('page')
    today = timezone.now().date()

    paginator = Paginator(comment_posts, 16)
    page_obj = paginator.get_page(page_number)
    return render(request, 'user/user_comment_posts.html', {'page_obj': page_obj, 'today': today})


def user_like_posts(request):
    posts = Post.objects.filter(like_users=request.user).order_by('-date')
    page_number = request.GET.get('page')
    today = timezone.now().date()

    paginator = Paginator(posts, 16)
    page_obj = paginator.get_page(page_number)
    return render(request, 'user/user_like_posts.html', {'page_obj': page_obj, 'today': today})


def user_delete(request):
    if request.method == 'POST':
        request.user.delete()
        return redirect('community:post_list')
    return render(request, 'user/user_profile')


def other_user_posts(request, author):
    posts = Post.objects.filter(author=author).order_by('-date')
    page_number = request.GET.get('page')
    today = timezone.now().date()

    paginator = Paginator(posts, 16)
    page_obj = paginator.get_page(page_number)
    return render(request, 'user/other_user_posts.html', {'page_obj': page_obj, 'author': User.objects.get(pk=author), 'today': today})


api_key = "06b36831-6622-49bc-a6f4-c1bc351edb1e"
headers = {"Content-Type": "application/json"}


def university_certification(request):
    schools = School.objects.all()
    if request.method == 'POST':
        email = request.POST["email"]
        univName = request.POST["univName"]
        code = request.POST.get('code')

        if code is None:
            url = "https://univcert.com/api/v1/certify"
            data = {
              "key" : api_key,
              "email" : email,
              "univName" : univName,
              "univ_check" : True
            }
        else:
            url = "https://univcert.com/api/v1/certifycode"
            data = {
              "key" : api_key,
              "email" : email,
              "univName" : univName,
              "code" : code,
            }
        json_data = json.dumps(data)
        response = requests.post(url, data=json_data, headers=headers)
        response_data = response.json()

        if(response_data["success"] and url == "https://univcert.com/api/v1/certify"):
            return render(request, 'user/university_certification.html', {'schools': schools, 'success': True, 'email': email, 'univName': univName})
        elif(response_data["success"] and url == "https://univcert.com/api/v1/certifycode"):
            request.user.university = response_data["univName"]
            request.user.save()
        else:
            return render(request, 'user/university_certification.html', {'schools': schools, 'error': response_data["message"]})
        return render(request, 'user/user_profile.html')
    return render(request, 'user/university_certification.html', {'schools': schools})
