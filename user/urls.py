from django.urls import path
from . import views

app_name = "user"

urlpatterns = [
    path('user_profile', views.user_profile, name='user_profile'),
    path('change_username', views.change_username, name='change_username'),
    path('user_profile/user_delete', views.user_delete, name='user_delete'),
]