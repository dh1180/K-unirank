from django.urls import path
from . import views

app_name = "user"

urlpatterns = [
    path('', views.user_profile, name='user_profile'),
    path('change_username', views.change_username, name='change_username'),
    path('user_posts/', views.user_posts, name='user_posts'),
    path('user_comment_posts/', views.user_comment_posts, name='user_comment_posts'),
    path('user_like_posts/', views.user_like_posts, name='user_like_posts'),
    path('user_profile/user_delete', views.user_delete, name='user_delete'),

    path('other_user_posts/<int:author>', views.other_user_posts, name='other_user_posts'),

    path('university_certification', views.university_certification, name='university_certification'),
]