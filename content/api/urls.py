from django.urls import path
from . import views

app_name = 'content_api'

urlpatterns = [
    path('video/', views.video_list_view, name='video_list'),
    path('video/<int:pk>/', views.video_detail_view, name='video_detail'),
]