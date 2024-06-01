from django.contrib.auth.models import User
from django.shortcuts import render, redirect


def user_profile(request):
    return render(request, 'user/user_profile.html')


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


def user_delete(request):
    if request.method == 'POST':
        request.user.delete()
        return redirect('community:post_list')
    return render(request, 'user/user_profile')