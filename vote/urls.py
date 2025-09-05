from django.urls import path
from . import views, views_vs


app_name = "vote"

urlpatterns = [
    path('', views.school_list, name='school_list'),
    path('school_list', views.redirect_school_list),  # 기존 /school_list는 /로 리다이렉트
    path('vote_page', views_vs.infinite_vs_view, name='vote_page')
]