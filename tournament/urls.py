from django.urls import path
from . import views


app_name = "tournament"

urlpatterns = [
    path('', views.create_tournament, name='create_tournament'),
    path('<int:tournament_id>', views.tournament_detail, name='tournament_detail'),
    path('match_result/<int:tournament_id>/<int:match_id>', views.tournament_match_result, name='tournament_match_result'),
    path('result', views.result, name='result'),
]