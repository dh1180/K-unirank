from django.urls import path
from . import views


app_name = "vote"

urlpatterns = [
    path('school_list', views.school_list, name='school_list'),
    path('upload', views.upload, name='upload'),
    path('jungsi_pdf_upload', views.jungsi_pdf_upload, name='jungsi_pdf_upload'),
    path('susi_pdf_upload', views.susi_pdf_upload, name='susi_pdf_upload'),
    path('', views.vote_page, name='vote_page'),
    path('donation', views.donation, name='donation'),
]