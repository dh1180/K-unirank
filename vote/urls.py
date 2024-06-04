from django.urls import path
from . import views


app_name = "vote"

urlpatterns = [
    path('', views.school_list, name='school_list'),
    path('school_score', views.school_score, name='school_score'),
    path('upload', views.upload, name='upload'),
    path('user_voted', views.user_voted, name='user_voted'),
    path('vote_delete/<int:school_pk>/<int:school_score_pk>', views.vote_delete, name='vote_delete'),
    path('user_delete', views.user_delete, name='user_delete'),
    path('jungsi_pdf_upload', views.jungsi_pdf_upload, name='jungsi_pdf_upload'),
    path('susi_pdf_upload', views.susi_pdf_upload, name='susi_pdf_upload'),
]