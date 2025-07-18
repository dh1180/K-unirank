from django.urls import path
from . import views


app_name = "vote"

urlpatterns = [
    path('school_list', views.school_list, name='school_list'),
    path('', views.vote_page, name='vote_page'),
]